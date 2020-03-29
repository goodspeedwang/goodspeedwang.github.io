import sys, os
import markdown2

def main(argv):
    filename = argv[1]
    dirname, _ = os.path.split(filename)
    #print(dirname,filename)
    md = read(filename)
    html = markdown2.markdown(md)
    write(filename.replace(".md",".html"),html)


def read(filename):
    with open(filename, 'r') as f:
        return f.read()

def write(filename, content):
    with open(filename, "w") as f:
        f.write(content)

if __name__ == "__main__":
    main(sys.argv)