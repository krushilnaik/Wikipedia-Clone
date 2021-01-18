import re
from django.shortcuts import render

from . import util


def index(request):
	return render(request, "encyclopedia/index.html", {
		"entries": util.list_entries()
	})

def entry(request, title):
	def createTag(tagType, content, **kwargs):
		attributes = " ".join([f"{k}=\"{v}\"" for k, v in kwargs.items()])
		return f"<{tagType}{' ' + attributes if attributes else ''}>{content}</{tagType}>"

	anchorRegex     = re.compile(r"(\[.+?\]\(.+?\))")
	italicRegex     = re.compile(r"( [*_]{1}[^*_]+?[*_]{1})")
	boldRegex       = re.compile(r"( [*_]{2}[^*_]+?[*_]{2})")
	boldItalicRegex = re.compile(r"( [*_]{3}[^*_]+?[*_]{3})")
	listItemRegex   = re.compile(r"^( *[*-]{1} .+)")
	headerRegex     = re.compile(r"^(#{1,6} .+)")

	regexList = [
		anchorRegex,
		boldItalicRegex,
		boldRegex, italicRegex,
		headerRegex, listItemRegex,
	]

	masterRegex = "|".join([regex.pattern for regex in regexList])
	masterRegex = re.compile(masterRegex)

	content = ""

	previousListLevel = -1
	with open(f"./entries/{title}.md", "r") as data:
		for line in data:
			tagFound = False
			if not line.rstrip():
				continue
			matches = masterRegex.split(line.rstrip())
			for match in matches:
				if not match:
					continue
				if headerRegex.match(match):
					tagFound = True
					cutoff = match.index("# ") + 1
					content += createTag(f"h{cutoff}", match[cutoff+1:])
				elif boldItalicRegex.match(match):
					tagFound = True
					content += createTag(
						"strong",
						createTag("em", match.strip()[3:-3])
					)
				elif boldRegex.match(match):
					tagFound = True
					content += createTag("strong", match.strip()[2:-2])
				elif italicRegex.match(match):
					tagFound = True
					content += createTag("em", match.strip()[1:-1])
				elif anchorRegex.match(match):
					tagFound = True
					text = match[1:match.index("]")]
					link = match[match.index("(")+1:-1]
					content += createTag("a", text, href=link)
				elif listItemRegex.match(match):
					tagFound = True
					currentListLevel = 0
					while match[currentListLevel] == " ":
						currentListLevel += 1
					currentListLevel //= 2
					if currentListLevel > previousListLevel:
						content += "<ul>"
					elif currentListLevel < previousListLevel:
						content += "</ul>"
					content += createTag("li", match[currentListLevel*2+2:])
					previousListLevel = currentListLevel
				elif previousListLevel != -1:
					for _ in range(previousListLevel + 1):
						previousListLevel -= 1
						content += "</ul>"
				elif tagFound:
					content += createTag("span", match)

			if not tagFound:
				content += createTag("p", line.rstrip())

	return render(request, "encyclopedia/entry.html", {
		"title": title,
		"content": content
	})
