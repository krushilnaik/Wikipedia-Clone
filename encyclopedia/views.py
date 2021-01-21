import re, random

from django.http.response import HttpResponseRedirect
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext as _
from django.shortcuts import render
from django import forms

from . import util

def validate_unique(value):
	if value in util.list_entries():
		raise ValidationError(
			_('%(value)s page already exists'),
			params={'value': value},
		)

class CreatePageForm(forms.Form):
	pageTitle = forms.CharField(
		label="", validators=[validate_unique],
		widget=forms.TextInput(
			attrs = {
				"placeholder": "Page title:",
				"style": "width: 20em; margin-bottom: 5px;"
			}
		)
	)

	pageContent = forms.CharField(
		label="", widget=forms.Textarea(
			attrs = {
				"placeholder": "Page content:",
				"style": "margin-bottom: 5px;"
			}
		)
	)

class EditPageForm(forms.Form):
	pageContent = forms.CharField(
		label="",
		widget=forms.Textarea()
	)

def index(request):
	return render(request, "encyclopedia/index.html", {
		"entries": util.list_entries()
	})

def entry(request, title):
	anchorRegex     = re.compile(r"(\[.+?\]\(.+?\))")
	italicRegex     = re.compile(r"([*_][^ ]{1}[^*_]+?[^ ][*_]{1})")
	boldRegex       = re.compile(r"([*_][^ ]{2}[^*_]+?[^ ][*_]{2})")
	boldItalicRegex = re.compile(r"([*_][^ ]{3}[^*_]+?[^ ][*_]{3})")
	listItemRegex   = re.compile(r"^( *[*-]{1} .+)")
	headerRegex     = re.compile(r"^(#{1,6} .+)")
	codeRegex       = re.compile(r"(```.*?```)")
	taskRegex       = re.compile(r"(\[[ x]\])")
	strikeRegex     = re.compile(r"(~~[^ ].*[^ ]~~)")

	masterRegex = [
		anchorRegex, boldItalicRegex,
		boldRegex, italicRegex,
		codeRegex, taskRegex,
		strikeRegex
	]

	masterRegex = "|".join([regex.pattern for regex in masterRegex])
	masterRegex = re.compile(masterRegex)


	def createTag(tagType, content, **kwargs):
		attributes = " ".join([f"{k}=\"{v}\"" for k, v in kwargs.items()])
		return f"<{tagType}{' ' + attributes if attributes else ''}>{content}</{tagType}>"

	def parseLine(raw_string):
		htmlBuilder = ""

		matches = masterRegex.split(raw_string)

		for match in matches:
			if not match:
				continue
			if headerRegex.match(match):
				cutoff = match.index("# ") + 1
				htmlBuilder += createTag(f"h{cutoff}", match[cutoff+1:])
			elif taskRegex.match(match):
				htmlBuilder += f"<input type='checkbox' disabled {'checked' if match[1] == 'x' else ''}>"
			elif boldItalicRegex.match(match):
				htmlBuilder += createTag(
					"strong",
					createTag("em", match.strip()[3:-3])
				)
			elif boldRegex.match(match):
				htmlBuilder += createTag("strong", match.strip()[2:-2])
			elif italicRegex.match(match):
				htmlBuilder += createTag("em", match.strip()[1:-1])
			elif anchorRegex.match(match):
				text = match[1:match.index("]")]
				link = match[match.index("(")+1:-1]
				htmlBuilder += createTag("a", text, href=link)
			elif strikeRegex.match(match):
				htmlBuilder += createTag("del", match[2:-2])
			elif codeRegex.match(match):
				htmlBuilder += createTag("code", match[3:-3])
			else:
				htmlBuilder += createTag("span", match)

		return htmlBuilder

	content = ""
	data = util.get_entry(title).split("\n")
	previousListLevel = 0

	for line in data:
		if not line.rstrip():
			continue
		if previousListLevel != 0 or listItemRegex.match(line):
			currentListLevel = 0
			while line[currentListLevel] == " ":
				currentListLevel += 1
			currentListLevel //= 2
			if currentListLevel > previousListLevel:
				content += "<ul>"
			elif currentListLevel < previousListLevel:
				content += "</ul>"
			content += createTag(
				"li",
				parseLine(line[currentListLevel*2+2:])
			)
			previousListLevel = currentListLevel
		elif previousListLevel != 0:
			for _ in range(previousListLevel + 1):
				previousListLevel -= 1
				content += "</ul>"
		else:
			content += createTag("div", parseLine(line))

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

	if request.method == "POST" and form.is_valid():
		title = form.cleaned_data["pageTitle"]
		content = form.cleaned_data["pageContent"]

		# These quotation characters were causing problems
		# replace them with a "normal" version
		content = content.replace("“", "\"")
		content = content.replace("”", "\"")
		content = content.replace("’", "'")

		util.save_entry(title, content.replace("\r\n", "\n"))

		return HttpResponseRedirect(title)

	return render(request, "encyclopedia/create_page.html", {
		"form": form
	})

def edit(request, title):
	form = EditPageForm(request.POST or {
		"pageContent": open(f"entries/{title}.md", "r").read()
	})

	if request.method == "POST" and form.is_valid():
		util.save_entry(title, form.cleaned_data["pageContent"].replace("\r\n", "\n"))

		return entry(request, title)
	
	return render(request, "encyclopedia/edit_page.html", {
		"form": form
	})

def search_results(request):
	allPages = util.list_entries()

	search = request.GET.get("q")

	if search in allPages:
		return HttpResponseRedirect(search)

	results = []

	for page in allPages:
		if search in page:
			results.append(page)
	
	return render(request, "encyclopedia/search_results.html", {
		"results": results
	})
