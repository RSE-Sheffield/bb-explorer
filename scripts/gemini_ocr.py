import google.generativeai as genai
import pathlib
import PIL.Image
import os, re, random, time

"""
This script uses Google's Gemeni AI API for performing OCR of
pages of the BB, from in_directory to out_directory (hardcoded paths)

Google keeps changing the available models, so this isn't the most stable

A little bit of post-processing is done to standardise some inconsistencies between responses.

There are also issues, such as inconsistent line wrapping which have been manually handled so far.

Page numbers are manually set, as OCR was making common mistakes
"""


# Configure your API key (https://aistudio.google.com/apikey?pli=1)
API_KEY = "REDACTED"  # Replace with your actual API key
genai.configure(api_key=API_KEY)

# Load the Gemini model
#model = genai.GenerativeModel('gemini-2.0-pro-exp-02-05')
model = genai.GenerativeModel('gemini-2.5-flash-preview-04-17')

gen_config = genai.types.GenerationConfig(
    temperature=1.0,  # Adjust the temperature value here (0.0 to 2.0)
    )

# Specify directory where image files can be found
in_directory = "images"
out_directory = "tex"
if not os.path.exists(out_directory):
    os.makedirs(out_directory)
    
# Build a list of image files
img_list = []

# Extract number
num_pattern = re.compile(r"([0-9]+).jpg")

# Iterate through items in the directory
for item in os.listdir(in_directory):
    item_path = os.path.join(in_directory, item)
    
    # Check if it's a file and add to the list
    if os.path.isfile(item_path):
        num = re.search(num_pattern, item).group(1)
        if num:
            img_list.append((int(num), item_path))
            
# Put the list in page order
img_list = sorted(img_list, key=lambda tup: tup[0])

# Process each image (use range, so we can resume later if error due to rate limit)
for i in range(0, len(img_list)):#len(img_list)):
    # Load image
    image = PIL.Image.open(img_list[i][1])
    # Write response to a text file
    out_path = os.path.join(out_directory, f"page{img_list[i][0]:03d}.tex")
    # Skip existing pages, to save free quota
    if os.path.exists(out_path):
        continue
    # Create a prompt that includes text and the image
    try:
        response = model.generate_content([
            """
Transcribe this 1800s French book page to plain text.
You should remove any wrapping, including resolving hyphenated words and mid-paragraph line breaks.
The page number should not be included.
If the page contains a running header/title it should not be included, these are centered text level in the page with the page number.
If it contains a section title that should be wrapped with a latex `\section{}`.
If you believe a word is incorrect you may correct it.
If the page contains any footnotes, typically marked in the form (1), they should be inlined where they are referenced with a latex `\footnote{}` not including the footnote's number.
(1) denotes a footnote.
If the page contains a table, include `\comment{table}` prior to the table’s transcription.
Do not include the page number in your transcription.
Do not include anything additional in your response which is not part of the original page.
If the page is empty, then your response should also be empty.
Do not respond with markdown.
Do not use additional latex commands which have not been discussed.
            """,
            image
        ], generation_config=gen_config)
        # This version is inconsistent on whether it wraps lines or not
        # response = model.generate_content([
            # """
# Transcribe this 1800s French book page to latex, your response should be purely latex.
# Wrap the lines, such that hyphenated words are resolved.
# If it contains a title that should be wrapped with a latex `\section{}`, however pages may contain headings which denote the current chapter that should not be interpreted as a title. You can deduce this from whether the first sentence appears to be the start of a paragraph.
# If you believe a word is incorrect you may correct it.
# If the page contains any footnotes, typically marked in the form (1), they should be inlined where they are referenced with a latex `\footnote{}` not including the footnote's number.
# (1) denotes a footnote.
# If the page contains a table, include `\comment{table}` prior to the table’s transcription.
# Do not include the page number in your transcription.
# Do not include anything additional in your response which is not part of the original page.
# If the page is empty, then your response should also be empty.
# Do not respond with markdown.
# Do not use additional latex commands which have not been discussed.
            # """,
            # image
        # ], generation_config=gen_config)
        #response = model.generate_content([
        #    "Transcribe this image to latex. It's written in 1800's French. Do not return anything except for the transcription. Do not include the page number. If a line is centered and all caps, it can be assumed to be a section title.",
        #    image
        #], generation_config=gen_config)
        #response = model.generate_content([
        #    "Transcribe this page please, centred text should be bold and the page number should not be included.",
        #     image
        # ], generation_config=gen_config)
        # Replace ſ with s in response
        clean_response = response.text.replace("ſ", "s")
        # Quotes are written as English quotes
        # OCR knowing it's French sometimes writes them as French quotes
        clean_response = clean_response.replace("« ", "\"")
        clean_response = clean_response.replace(" »", "\"")
        clean_response = clean_response.replace("«", "\"")
        clean_response = clean_response.replace("»", "\"")
        # Also sometimes misreads as other symbols/commas
        clean_response = clean_response.replace("“", "\"")
        clean_response = clean_response.replace("”", "\"")
        clean_response = clean_response.replace("„", "\"")
        clean_response = clean_response.replace("\n,,", "\n\"")
        clean_response = clean_response.replace(",,\n", "\"\n")
        clean_response = clean_response.replace(",,\r\n", "\"\r\n")
        f = open(out_path, "w", encoding="utf-8")
        f.write("\setcounter{page}{%d} "%(img_list[i][0]))
        f.write(clean_response)
        f.close()
        # Sleep for a bit, to not hit a rate limit quota
        # There's still a daily rate limit, but not clear what that threshold is
        time.sleep(random.randint(10, 10))
    except Exception as e:
      print(f"An exception occurred:\nat file[{i}] = {img_list[i]}\n{repr(e)}")
      break;
