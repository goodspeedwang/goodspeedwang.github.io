import sys, os
import markdown2
from jinja2 import Template

def main(argv):
    filename = argv[1]
    dirname,_ = os.path.split(filename)
    basename = dirname + "/base.html"
    while os.path.exists(basename) == False:
        parent = os.path.abspath(os.path.join(basename, "../.."))
        basename = parent + "/base.html"
    base_template = read(basename)
    template = Template(base_template)
    md = read(filename)
    markdown = markdown2.markdown(md)

    
    html = template.render(markdown=markdown)
    write(filename.replace(".md",".html"),html)


def read(filename):
    with open(filename, 'r') as f:
        return f.read()

def write(filename, content):
    with open(filename, "w") as f:
        f.write(content)

if __name__ == "__main__":
    main(sys.argv)