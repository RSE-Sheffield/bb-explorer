import re, os
from unidecode import unidecode # for removing accents for fuzzy comparisons

"""
Combine separate .tex files into a single output from in_directory to out_file
Remove false titles which have been parsed
Attempt to merge hard-wrapped lines
? detect if the tex is wrapped in markdown code block

It's still worth taking a minute to skim the final output for incorrect sections/wrapping
"""

in_directory = "row70 Des_Orcades_Et_Sethland"
out_file = "bb-Agriculture_Anglais-19-Agriculture-Des_Orcades_Et_Sethland-pg386-391_fr.tex"

# Build a list of image files
tex_list = []
output_txt = ""


num_pattern = re.compile(r"([0-9]+).tex")
page_pattern = re.compile(r"\\setcounter{page}{([0-9]+)}")
section_pattern1 = re.compile(r"(\\section{([A-Za-zÀ-ÿ][A-Za-z0-9À-ÿ' .]+)}[\n\r\s]+)")
section_pattern2 = re.compile(r"(([A-Z][A-Z0-9À-ÿ' .]+)[\n\r\s]+)")
page_pattern = re.compile(r"\\setcounter{page}{([0-9]+)}")

# Iterate through items in the directory
for item in os.listdir(in_directory):
    item_path = os.path.join(in_directory, item)
    
    # Check if it's a file and add to the list
    if os.path.isfile(item_path):
        num = re.search(num_pattern, item).group(1)
        if num:
            tex_list.append((int(num), item_path))
            
# Put the list in page order
tex_list = sorted(tex_list, key=lambda tup: tup[0])

prev_even_titles = set()
prev_odd_titles = set()
removed_titles = set()
# Process each page
for i in range(len(tex_list)):
    # Load page to a temporary buffer
    f = open(tex_list[i][1], "r", encoding="utf-8")
    temp_page = f.read()
    f.close()
    # Extract its page number   
    match = re.search(page_pattern, temp_page)
    page_num = int(match.group(1)) if match else -1
    # If page number does not match filename (due to ocr script using wrong number), replace
    if page_num != tex_list[i][0]:
        temp_page = temp_page.replace("\\setcounter{page}{%d}"%(page_num), "\\setcounter{page}{%d}"%(tex_list[i][0]))
    # @todo greater complexity, as there are some pages that don't have numbers where this will fall over.
    prev_page_num = page_num
    # Detect any titles
    titles = re.findall(section_pattern1, temp_page)
    for t in titles:
        t2 = unidecode(t[1].replace(" ", ""))
        if t2 in prev_even_titles or t2 in prev_odd_titles or t2 in removed_titles:
            # Remove titles that appeared on previous pages
            removed_titles.add(t2)
            temp_page = temp_page.replace(t[0], "")
    titles2 = re.findall(section_pattern2, temp_page)
    for t in titles2:
        t2 = unidecode(t[1].replace(" ", ""))
        if t2 in prev_even_titles or t2 in prev_odd_titles or t2 in removed_titles:
            # Remove titles that appeared on previous pages
            removed_titles.add(t2)
            temp_page = temp_page.replace(t[0], "")
    # todo, how to detect contracted titles after a new section begins?
    # todo, fuzzy match to catch titles where a character has been read incorrectly? (e.g. current example "." becomes ":")
    # Update title cache
    if page_num % 2 == 0:
        prev_even_titles = set()
        for i in titles:
            prev_even_titles.add(unidecode(i[1].replace(" ", ""))) # Some titles get OCRd with spaces between chars
        for i in titles2:
            prev_even_titles.add(unidecode(i[1].replace(" ", "")))
    else:
        prev_odd_titles = set()
        for i in titles:
            prev_odd_titles.add(unidecode(i[1].replace(" ", "")))
        for i in titles2:
            prev_odd_titles.add(unidecode(i[1].replace(" ", "")))
    # Weird footnote character
    temp_page = temp_page.replace("", "\\f")
    # Resolve any hyphenated words
    temp_page = temp_page.replace("-\r\n", "")
    temp_page = temp_page.replace("-\n", "")
    # Remove any markdown code blocks
    temp_page = temp_page.replace("```latex\r\n", "")
    temp_page = temp_page.replace("```latex\n", "")
    temp_page = temp_page.replace("\r\n```", "")
    temp_page = temp_page.replace("\n```", "")
    # Resolve any hard word wrapping
    temp_page = temp_page.replace("\r\n\r\n", "\r\n")
    if not "\r\n" in temp_page:
        temp_page = temp_page.replace("\n\n", "\n")
    # Append to output_txt
    #@todo handle if a word wraps over a page?
    output_txt += temp_page
    
# Write output
f = open(out_file, "w", encoding="utf-8")
f.write(output_txt)
f.close()