# C03 Antique reading note
Reader/extractor: /root/course_discovery/verify_new_scope; independently re-read by /root/course_discovery.
URL: https://raw.githubusercontent.com/IOAI-official/IOAI-2025/main/Individual-Contest/Antique/Antique.ipynb
Read extent: raw lines 19–72, statement markdown cell a4c6054c-d42b-4c2b-bb79-deb64d936c24.
There are five feature columns and a label column. Label 1 means authentic, -1 replica, and 0 unknown. Unknown is not a confirmed negative class. Outputs must contain -1 or 1, with the stated file and header contract; accuracy divides correct predictions by all evaluated examples.
The task motivates using unknown-label training samples. An introductory known-label-only supervised example can teach a boundary, but does not solve the complete semi-supervised problem.
Observable introductory demand: classify unknown/negative/positive correctly, exclude target columns from features, and preserve the permitted output-label set in an independent new table.
This is a paraphrased reading note, not original notebook bytes. No contest data/model execution or performance measurement occurred.
