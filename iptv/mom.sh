filename=iptv/mom.m3u8
echo '#EXTM3U' > $filename
cat iptv/_includes/oversee.stable.m3u >> $filename; echo -e '\n' >> $filename
#cat iptv/_includes/cctv.stable.m3u >> $filename; echo -e '\n' >> $filename
cat iptv/_includes/provinces.stable.m3u >> $filename; echo -e '\n' >> $filename
cat iptv/_includes/movie.m3u >> $filename; echo -e '\n' >> $filename

