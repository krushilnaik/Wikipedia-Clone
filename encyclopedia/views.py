import re, random
from django.http.response import HttpResponseRedirect
from django.shortcuts import render
from django import forms

from . import util

class CreatePageForm(forms.Form):
	pageTitle = forms.CharField(label="")
	pageContent = forms.CharField(label="", widget=forms.Textarea(attrs={
		"placeholder": "Page content:"
	}))

def index(request):
	return render(request, "encyclopedia/index.html", {
		"entries": util.list_entries()
	})

def entry(request, title):
	def createTag(tagType, content, **kwargs):
		attributes = " ".join([f"{k}=\"{v}\"" for k, v in kwargs.items()])
		return f"<{tagType}{' ' + attributes if attributes else ''}>{content}</{tagType}>"

	anchorRegex     = re.compile(r"(\[.+?\]\(.+?\))")
	italicRegex     = re.compile(r"([*_]{1}[^*_]+?[*_]{1})")
	boldRegex       = re.compile(r"([*_]{2}[^*_]+?[*_]{2})")
	boldItalicRegex = re.compile(r"([*_]{3}[^*_]+?[*_]{3})")
	listItemRegex   = re.compile(r"^( *[*-]{1} .+)")
	headerRegex     = re.compile(r"^(#{1,6} .+)")
	codeRegex       = re.compile(r"(```.*```)")

	regexList = [
		anchorRegex,
		boldItalicRegex,
		boldRegex, italicRegex,
		headerRegex, listItemRegex,
		codeRegex
	]

	masterRegex = "|".join([regex.pattern for regex in regexList])
	masterRegex = re.compile(masterRegex)

	content = ""

	data = util.get_entry(title).split("\n")

	previousListLevel = -1
	for line in data:
		if not line.rstrip():
			continue
		matches = masterRegex.split(line.rstrip())
		for match in matches:
			if not match:
				continue
			if headerRegex.match(match):
				cutoff = match.index("# ") + 1
				content += createTag(f"h{cutoff}", match[cutoff+1:])
			elif boldItalicRegex.match(match):
				content += createTag(
					"strong",
					createTag("em", match.strip()[3:-3])
				)
			elif boldRegex.match(match):
				content += createTag("strong", match.strip()[2:-2])
			elif italicRegex.match(match):
				content += createTag("em", match.strip()[1:-1])
			elif anchorRegex.match(match):
				text = match[1:match.index("]")]
				link = match[match.index("(")+1:-1]
				content += createTag("a", text, href=link)
			elif codeRegex.match(match):
				content += createTag("code", match[3:-3])
			elif listItemRegex.match(match):
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
			else:
				content += createTag("span", match)

	return render(request, "encyclopedia/entry.html", {
		"title": title,
		"content": content
	})

def random_page(request):
	entries = util.list_entries()
	redirect = random.choice(entries)
	return entry(request, redirect)

def create_page(request):
	form = CreatePageForm(request.POST or None)

	# TODO: error message when trying to create a page that already exists

	if request.method == "POST" and form.is_valid():
		title = form.cleaned_data["pageTitle"]
		content = form.cleaned_data["pageContent"]
		util.save_entry(title, content)

		return HttpResponseRedirect(title)

	return render(request, "encyclopedia/create_page.html", {
		"form": form
	})
