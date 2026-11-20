import { DatabaseSync } from "node:sqlite";
import { randomUUID } from "node:crypto";

export function openLedger(filename) {
  const db=new DatabaseSync(filename);
  db.exec("PRAGMA journal_mode=WAL; PRAGMA synchronous=FULL; PRAGMA busy_timeout=10000;");
  db.exec("CREATE TABLE IF NOT EXISTS jobs (key TEXT PRIMARY KEY, revision INTEGER NOT NULL, body TEXT NOT NULL);" +
    "CREATE TABLE IF NOT EXISTS heads (week INTEGER PRIMARY KEY, hash TEXT NOT NULL, body TEXT NOT NULL);" +
    "CREATE TABLE IF NOT EXISTS versions (week INTEGER, hash TEXT, body TEXT NOT NULL, PRIMARY KEY(week,hash));" +
    "CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY, week INTEGER, key TEXT, entry TEXT NOT NULL);" +
    "CREATE TABLE IF NOT EXISTS calls (id TEXT PRIMARY KEY, hash TEXT NOT NULL, response TEXT NOT NULL);" +
    "CREATE TABLE IF NOT EXISTS inflight (id TEXT PRIMARY KEY, hash TEXT NOT NULL);" +
    "CREATE TABLE IF NOT EXISTS lease (slot INTEGER PRIMARY KEY, owner TEXT NOT NULL, expires INTEGER NOT NULL);");
  const token=randomUUID();
  function transact(action) {
    db.exec("BEGIN IMMEDIATE");
    try { const result=action(); db.exec("COMMIT"); return result; }
    catch(e){ db.exec("ROLLBACK"); throw e; }
  }
  function decode(row) {return row ? JSON.parse(row.body) : null;}
  function guard(){
    const lock=db.prepare("SELECT owner,expires FROM lease WHERE slot=1").get();
    if(!lock||lock.owner!==token||lock.expires<=Date.now())throw new Error("Lost course run lease");
  }
  return {
    acquire(ttl=120000) {
      transact(()=>{
        const old=db.prepare("SELECT owner, expires FROM lease WHERE slot=1").get();
        if(old && old.expires>Date.now())throw new Error("Another controller owns this run");
        db.prepare("INSERT OR REPLACE INTO lease VALUES(1,?,?)").run(token,Date.now()+ttl);
      });
    },
    renew(){
      const changed=db.prepare("UPDATE lease SET expires=? WHERE slot=1 AND owner=? AND expires>?").run(Date.now()+120000,token,Date.now());
      if(!changed.changes)throw new Error("Lost course run lease");
    },
    release(){db.prepare("DELETE FROM lease WHERE slot=1 AND owner=?").run(token);},
    close(){db.close();},
    read(key){return decode(db.prepare("SELECT body FROM jobs WHERE key=?").get(key));},
    head(week){return decode(db.prepare("SELECT body FROM heads WHERE week=?").get(week));},
    history(week,hash){return decode(db.prepare("SELECT body FROM versions WHERE week=? AND hash=?").get(week,hash));},
    save(key,from,state,event,accepted=null){
      transact(()=>{
        guard();
        const present=db.prepare("SELECT revision FROM jobs WHERE key=?").get(key);
        if((present?.revision??0)!==from)throw new Error("Journal changed concurrently");
        if(accepted){
          const head=db.prepare("SELECT hash FROM heads WHERE week=?").get(accepted.week);
          if((head?.hash??null)!==accepted.previous)throw new Error("Candidate baseline advanced");
          for(const [week,binding] of Object.entries(accepted.dependencies)){
            const p=decode(db.prepare("SELECT body FROM heads WHERE week=?").get(Number(week)));
            if(p?.hash!==binding.hash || p?.input!==binding.input)throw new Error("Prerequisite changed before adoption");
          }
          const body=JSON.stringify(accepted);
          db.prepare("INSERT OR IGNORE INTO versions VALUES(?,?,?)").run(accepted.week,accepted.hash,body);
          db.prepare("INSERT OR REPLACE INTO heads VALUES(?,?,?)").run(accepted.week,accepted.hash,body);
        }
        db.prepare("INSERT OR REPLACE INTO jobs VALUES(?,?,?)").run(key,state.revision,JSON.stringify(state));
        db.prepare("INSERT INTO events(week,key,entry) VALUES(?,?,?)").run(state.week,key,JSON.stringify(event));
      });
    },
    receipt(id,hash){
      const r=db.prepare("SELECT hash,response FROM calls WHERE id=?").get(id);
      if(r && hash!==r.hash)throw new Error("Frozen request content changed");
      return r ? JSON.parse(r.response) : null;
    },
    reserve(id,hash){
      return transact(()=>{
        guard();
        const known=db.prepare("SELECT hash,response FROM calls WHERE id=?").get(id);
        if(known){
          if(known.hash!==hash)throw new Error("Frozen request content changed");
          return {recorded:true,response:JSON.parse(known.response)};
        }
        const pending=db.prepare("SELECT hash FROM inflight WHERE id=?").get(id);
        if(pending)throw new Error("Uncertain external call "+id+"; inspect pending-calls before resuming");
        db.prepare("INSERT INTO inflight VALUES(?,?)").run(id,hash);
        return {recorded:false};
      });
    },
    remember(id,hash,response){
      transact(()=>{
        guard();
        const old=db.prepare("SELECT hash FROM inflight WHERE id=?").get(id);
        if(!old||old.hash!==hash)throw new Error("Missing matching call reservation");
        db.prepare("INSERT INTO calls VALUES(?,?,?)").run(id,hash,JSON.stringify(response));
        db.prepare("DELETE FROM inflight WHERE id=?").run(id);
      });
    },
    pending(){return db.prepare("SELECT id,hash FROM inflight ORDER BY id").all().map(r=>({...r}));},
    resolveCall(evidence){
      transact(()=>{
        guard();
        const {id,hash,outcome,reason}=evidence;
        const old=db.prepare("SELECT hash FROM inflight WHERE id=?").get(id);
        if(!old||old.hash!==hash||!["absent","recovered"].includes(outcome)||typeof reason!=="string"||!reason.trim())throw new Error("No matching external recovery evidence");
        if(outcome==="recovered"){
          if(!evidence.response||typeof evidence.response!=="object")throw new Error("Missing original worker response");
          db.prepare("INSERT INTO calls VALUES(?,?,?)").run(id,hash,JSON.stringify(evidence.response));
        }
        db.prepare("DELETE FROM inflight WHERE id=?").run(id);
        db.prepare("INSERT INTO events(week,key,entry) VALUES(?,?,?)").run(0,id,JSON.stringify({kind:"call_recovery",outcome,reason}));
      });
    },
    events(){return db.prepare("SELECT id,week,key,entry FROM events ORDER BY id").all().map(r=>({...r,entry:JSON.parse(r.entry)}));}
  };
}
