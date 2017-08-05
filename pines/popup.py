_string_gotten = ""

def get_string(caption="Prompt:", default_value="default value"):
	global _string_gotten
	from tkinter import Tk, Entry, Button, mainloop, END, Label, LEFT

	master = Tk()

	def makeentry(parent, caption_, width=None, **options):
		Label(parent, text=caption_).pack(side=LEFT)
		entry = Entry(parent, **options)
		if width:
			entry.config(width=width)
		entry.pack(side=LEFT)
		return entry

	e = makeentry(master, caption, width=50)
	e.pack()

	e.delete(0, END)
	e.insert(0, default_value)
	e.focus_set()

	def callback():
		global _string_gotten
		_string_gotten = (e.get()) # This is the text you may want to use later
		master.destroy()

	b = Button(master, text = "OK", width = 10, command = callback)
	b.pack()
	mainloop()
	return _string_gotten


