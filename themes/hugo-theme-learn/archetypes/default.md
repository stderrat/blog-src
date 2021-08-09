+++
title = "{{ replace .Name "-" " " | title }}"
date =  {{ .Date }}
weight = 5
+++

Lorem Ipsum.

--- 
title: "{{ replace .Name "-" " " | title }}"
date: {{ .Date }}
doctype: book

weight: 10

author: TnT
draft: true

type: post
categories:
   - A
   - B
   - C
tags:
   - Hugo
   - Game Development
   - Internet of Things (IoT)
   - Linux
   - ...
---

:imagesdir: /posts/service-mesh/images/
:icons: font
:toc: