<?xml version="1.0" encoding="utf-8"?>
<stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
	<output method="html" encoding="utf-8" doctype-public="-//W3C//DTD XHTML 1.0 Transitional//EN" doctype-system="http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd" />
	<template match="导航">
		<html lang="zh-cn">
			<head>
				<meta charset="UTF-8" />
				<meta name="viewport" content="width=device-width" />
				<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
				<title>
					导航
				</title>
				<base target="_blank" />
				<style>
					body{background-color:#C0C0C0; margin:0px;}
					a{color:blue;text-decoration:none;font-size:10pt;padding:3px 3px;}
					div{letter-spacing:0.02em; line-height:1.3;COLOR: "#666666"; padding:2px 0px;}
					.title{background-color: #4455aa;color: white;font-size: 12px;font-weight:bold;height:20;text-align: left;}
				</style>
				<link href="/favicon.ico" rel="icon" />
			</head>
			<body>
				<apply-templates select="组" />
			</body>
		</html>
	</template>
	<template match="组">
		<div class="title">
			-=>
			<value-of select="@组名" />
		</div>
		<div>
			<apply-templates select="网址" />
		</div>
	</template>
	<template match="网址">
		<a>
			<attribute name="href">
				<value-of select="地址" />
			</attribute>
			<value-of select="名称" />
		</a>
	</template>
</stylesheet>
