import requests
import csv
import re
import os
import time 


# LINK = ["https://www.youtube.com/watch?v=SEnd9g3nXPY&feature=youtu.be",
# 		"https://youtu.be/Q1YyPNF_iow",
# 		"https://youtu.be/X64nYvzzbkA",
# 		"https://youtu.be/zZP1-eqLqzE",
# 		"https://youtu.be/fhQggsdDjcQ",
	# ]
# SLICES = {
# 	"vid_id": slice(1, 2),
# }
RE_CACHES = {
	"vid_id_comf" : re.compile(r'v=([a-zA-Z0-9_]+)'),
	"vid_id_bef" : re.compile(r'.be/([a-zA-Z0-9_]+)'),
	"utm_link" : re.compile(r'https://utm.guru/([_\w]{5})'),
	"utm_campaign" : re.compile(r'utm_campaign=(.*?)(&utm_|$)')
}

def get_vid_from_link(link: str = None) -> str:
	if not isinstance(link, str):
		raise ValueError("Expected a link")
	else:
		if "watch" in link:
			return re.search( RE_CACHES.get("vid_id_comf"), link ).group(1)
		else:
			return re.search( RE_CACHES.get("vid_id_bef"), link ).group(1)

def save_page(link: str = None) -> None:
	if not isinstance(link, str):
		raise ValueError("Expeced a link")
	else:
		vid = get_vid_from_link(link)
		if not os.path.exists(f'{vid}.txt'):
			with open(f'{vid}.txt', 'a', encoding="UTF-8") as file:
				file.write( requests.get(link).text)

def search_in_page(link: str = None, key: str = None) -> None:
	matches = set()
	if not isinstance(link, str) or (key not in RE_CACHES):
		print(f'Link: {link} Key: {key}')
		raise ValueError("Wrong link format or search pattern")
	else:
		save_page(link)
		vid = get_vid_from_link(link)
		with open(f'{vid}.txt', encoding="UTF-8") as file:
			for line in file:
				tmp = re.findall(RE_CACHES.get(key), line)
				if tmp:
					matches.update(tmp)
	return matches

def main_driver():
	if not os.path.exists("input.csv") :
		print("Create input.csv file first")
	else:
		with open("input.csv", "r", newline='') as input_file, open("output.csv", "w", newline='') as out_file:
			reader = csv.DictReader(input_file)
			# with open("output.csv", "w") as out_file:
			header = ['LINK', 'CAMP']
			writer = csv.DictWriter(out_file, fieldnames=header)
			writer.writeheader()
			ITER = 1
			for attr in reader:
				codes = search_in_page(attr['LINK'], "utm_link")
				camps = set()
				for code in codes:
					new_link = "https://utm.guru/" + code
					time.sleep(2.5)
					camps.add( re.search( RE_CACHES.get("utm_campaign"), requests.get(new_link).url).group(1) )
				SUB=1
				for camp in camps : 
					data = {
						'LINK' : attr['LINK'],
						'CAMP' : camp,
					}
					writer.writerow(data)
					print(f'DONE {ITER} {SUB}')
					SUB += 1
				ITER += 1
				os.remove( f'{get_vid_from_link(attr["LINK"])}.txt' )

if __name__ == "__main__":
	main_driver()