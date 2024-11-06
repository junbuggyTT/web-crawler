from collections import defaultdict
import json
import tkinter as tk

class SimpleGUI:
    def __init__(self, master):
        self.master = master
        master.title("CS 121 Index")

        self.input_label = tk.Label(master, text="Enter a string:")
        self.input_label.pack()

        self.input_entry = tk.Entry(master)
        self.input_entry.pack()

        self.query_button = tk.Button(master, text="Query", command=self.query)
        self.query_button.pack()

        self.output_label = tk.Label(master, text="Output:")
        self.output_label.pack()

        self.output_text = tk.Text(master, height=60, width=180)
        self.output_text.pack()
        
        # Reading index
        with open("/Users/junyoon/Downloads/CS121/Project2StarterCode/finalindex1gram.json", "r") as file:
            bigdict = json.load(file)
            self.tfidfs = bigdict['tfidfs']
            self.webpages = bigdict['webpages']
        
        with open("/Users/junyoon/Downloads/CS121/Project2StarterCode/bigramindex.json", "r") as file:
            bigdict = json.load(file)
            self.bigram_tfidfs = bigdict['tfidfs']
            self.bigram_webpages = bigdict['webpages']

    # Retrieve links from bookkeeping.json
        with open("/Users/junyoon/Downloads/WEBPAGES_RAW/bookkeeping.json", "r") as file:
            self.links = json.load(file)

    def query(self):
        input_string = self.input_entry.get()

        # Call the query method with the input string
        output_string = query(input_string, self.tfidfs, self.bigram_tfidfs, self.webpages, self.links)
        
        # Display the output in the output_text box
        self.output_text.delete(1.0, tk.END)
        self.output_text.insert(tk.END, output_string)

def query(input_string, index, bigram_index, pages, links):
    try:
        msg = 'Top 20 Links\n\n'

        all_related_pages = defaultdict(float)

        inputs = input_string.split()
        bigram_inputs = []
        for i in range(len(inputs)-1):
            bigram = ' '.join(inputs[i:i+2])
            bigram_inputs.append(bigram)

        for word in inputs:
            related_pages = index[word.lower()]
            for page, _ in related_pages.items():
                if input_string in pages[page]['title']:
                    related_pages[page] = related_pages[page] * 100
                if input_string in pages[page]['heading']:
                    related_pages[page] = related_pages[page] * 100
                if input_string in pages[page]['bold']:
                    related_pages[page] = related_pages[page] * 1000

                all_related_pages[page] = all_related_pages.get(page, 0) + related_pages[page]
        
        for bigram in bigram_inputs:
            if bigram in bigram_index.keys():
                for page_id in bigram_index[bigram].keys():
                    if page_id in all_related_pages.keys():
                        all_related_pages[bigram_index[bigram]] = all_related_pages.get([bigram_index[bigram]], 0) * 10000
        
        all_related_pages = dict(sorted(all_related_pages.items(), key = lambda item: item[1], reverse = True))

        num_of_links = 0
        for key in all_related_pages.keys():
            msg += f'{links[key]}\n'
            if pages[key]['title'].strip() == '':
                msg+= f'Title words: No title\n'
            else:
                msg+= f'Title words: {pages[key]["title"]}\n'
            
            if pages[key]['heading'].strip() == '':
                msg+= f'Header words: No header words\n'
            else:
                first_ten = ' '.join(pages[key]["heading"].split()[:min(10, len(pages[key]["heading"].split()))])
                msg+= f'Header words: {first_ten}\n'

            if pages[key]['bold'].strip() == '':
                msg+= f'Bolded words: No words bolded\n\n'
            else:
                first_ten = ' '.join(pages[key]["bold"].split()[:min(10, len(pages[key]["bold"].split()))])
                msg+= f'Bolded words: {first_ten}\n\n'
        
            num_of_links += 1
            if num_of_links == 20:
                break
        return msg
    
    except KeyError:
        return 'Word not found in any documents'

def main():
    root = tk.Tk()
    gui = SimpleGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
