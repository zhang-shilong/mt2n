# Multi-table to Network

### 背景

[Karma](https://github.com/usc-isi-i2/Web-Karma) 工具可以使用本体对数据进行标注，但 Karma 也存在以下两点不足：

- 只能标注单表数据，不能标注多表数据；
- 使用 SQL 导入多表需要建立 JOIN 关系，容易产生大量冗余数据。

因此，我们需要开发一种支持多表标注且冗余数据量小的多表标注算法。

### 介绍

Multi-table to Network (MT2N) 输入 Karma 导出的 RDF 文件，输出 JSON 格式的图。

MT2N 支持以下功能：

- 实体类型和表的对应关系可以是一对一、一对多或多对一。即每张表中可以存在多个实体类型，每个实体类型可以存在于多张表内。
- 更加灵活的实体整合方式。相较于 SQL 严格的主外码关系，MT2N 没有严格的主外键关系。
- 低冗余数据。MT2N 的结果是一张图网络，这种存储方式比表格具有更少的冗余数据，且利于分析。

### 输入

TXT 文件（每行包含一个路径，对应一个 Karma 导出的 RDF 文件）。

### 输出

1. 图网络 JSON 文件

   格式如下：

   ```json
   {"Vertices":[
   	{"id":0,"entity_type":0,"properties":"{'model': 'ChrSy.fgenesh.mRNA.1',..."},
   	{}
   ]},
   {"Edges":[
   	{"source_id":1000,"target_id":3,"relationship":0},
   	{}
   ]}
   ```

2. 实体与关系编号的对应文件
   
   格式如下：
   
   ```
   Gene	0
   Go_classification	1
   
   PartOf	0
   ```
