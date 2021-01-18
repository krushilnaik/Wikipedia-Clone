import re
# from typing import Match
from django.shortcuts import render

from . import util


def index(request):
	return render(request, "encyclopedia/index.html", {
		"entries": util.list_entries()
	})


def entry(request, title):
	# def md2html(markdown):
	# 	return

	def createTag(tagType, content, **kwargs):
		attributes = " ".join([f"{k}={v}" for k, v in kwargs.items()])
		return f"<{tagType} {attributes if attributes else ''}>{content}</{tagType}>"

	linkRegex = re.compile(r"(\[.+?\]\(.+?\))")
	italicRegex =     re.compile(r"( [*_]{1}[^*_]+?[*_]{1})")
	boldRegex =       re.compile(r"( [*_]{2}[^*_]+?[*_]{2})")
	boldItalicRegex = re.compile(r"( [*_]{3}[^*_]+?[*_]{3})")
	listRegex = re.compile(r"([*-]{1} .+)")
	hRegex = re.compile(r"^(#{1,6} .+)")

	regexList = {
		"a": linkRegex,
		"em strong": boldItalicRegex,
		"strong": boldRegex,
		"em": italicRegex,
		"h": hRegex,
		"li": listRegex,
	}

	content = ""

	previousListLevel = 0
	with open(f"./entries/{title}.md", "r") as data:
		for line in data:
			if not line:
				continue
			for tag, regex in regexList.items():
				current = regex.split(line)
				if len(current) > 1:
					if tag == "a":
						pass
					elif tag == "li":
						currentListLevel = len(current[1]) // 2

						if currentListLevel > previousListLevel:
							previousListLevel += 1
							content += "<ul>"
						elif currentListLevel < previousListLevel:
							content += "</ul>"*(previousListLevel - currentListLevel)

						content += createTag("li", current[-2])
					else:
						pass

	return render(request, "encyclopedia/entry.html", {
		title: title,
		content: content
	})
