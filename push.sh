#! /bin/bash
# python3 ./build.py

# 缓存破坏：根据 piggybank.js 内容计算哈希，注入 html 的 ?v= 参数
# 这样每次 JS 内容变化，浏览器都会强制重新拉取，避免看旧版本
if [ -f piggybank.js ] && [ -f piggybank.html ]; then
  if command -v md5 >/dev/null 2>&1; then
    HASH=$(md5 -q piggybank.js)
  else
    HASH=$(md5sum piggybank.js | cut -d' ' -f1)
  fi
  HASH=${HASH:0:8}
  sed -i '' -E "s|(piggybank\.js\?v=)[A-Za-z0-9_]*|\1${HASH}|" piggybank.html
fi

git pull --rebase --autostash
git add .
git commit -a -m "`date +%Y%m%e%H%M%S`"
git push