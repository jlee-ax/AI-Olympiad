# C02 Pixel reading note
Reader/extractor: /root/course_discovery/verify_new_scope; independently re-read by /root/course_discovery.
URL: https://raw.githubusercontent.com/IOAI-official/IOAI-2025/main/Individual-Contest/Pixel/Pixel.ipynb
Read extent: raw lines 28–90; extractor additionally read displayed 94–96. Markdown cell 4509a190.
Input images are 224 by 224 and have tracking IDs. Output one rectangle per image, top/left inclusive and bottom/right exclusive; at most 6.25 percent of original pixels may be retained. The resulting maximum is 3136 pixels. The output notebook must generate the specified JSONL file.
Observable demand: predict the selected pixel set and (bottom-top)*(right-left), then check boundary, over-budget and file-contract cases on new coordinates. A valid rectangle does not establish CLIP classification quality.
The statement also specifies provided CLIP/data only, an added other class and an eight-minute runtime for 698 test images. They were read, but no dataset/model/runtime experiment was performed.
Empty rectangles and coordinate dtype acceptance were not settled in this read extent. This is a paraphrased reading note, not fetched notebook bytes or an authenticated original snapshot.
