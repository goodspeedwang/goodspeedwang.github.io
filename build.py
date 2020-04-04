# -*- coding: utf-8 -*-  

import os, re

def read_title(filename):
    file = open(filename, 'r', encoding='utf-8')

    try:
        return file.readline().replace("#","").strip()
    finally:
        file.close()
    return None


def make_sidebar(filepath, content):
    sidebar_path = os.path.join(filepath,"_sidebar.md")
    fo = open(sidebar_path, "w", encoding='utf-8')
    fo.write( content )
    # 关闭文件
    fo.close()

def find(parent, lines, dirs=[]):
    files = [(f, os.path.join(parent, f)) for f in os.listdir(parent) if f[0] != "." and f[0] != "_"]
    
    # 处理目录
    for filename, fullname in files:
        if os.path.isdir(fullname):
            if len(dirs) == 0 and re.match("^\\d+?\\.", filename) == None:
                continue
            child = os.path.join(parent, filename)
            lines.append(make_line(True, filename, fullname, dirs))
            find(child, lines, dirs + [filename]) 
            

    # 处理文件
    for filename, fullname in files:
        if os.path.isdir(fullname) == False and os.path.splitext(filename)[1] == '.md':
            fullname = os.path.join(parent, filename)
            lines.append(make_line(False, filename, fullname, dirs))


def make_line(isdir, filename, fullname, dirs):
    tab = "    " * len(dirs)
    line = "{0}- {1}"
    if isdir:
        line = line.format(tab, filename)
    else: 
        name = read_title(fullname)
        link = "/" + "/".join(dirs + [filename])
        line = "{0}- [{1}]({2})".format(tab, name, link)
    return line
    

def main():
    root = os.path.abspath(os.path.dirname(__file__))
    lines = []
    find(root, lines)
    make_sidebar(root,"\n".join(lines) )
    # print(markdowns)

if __name__ == "__main__":
    main()