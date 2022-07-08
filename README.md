# Multi-table to Network

## 背景

[Karma](https://github.com/usc-isi-i2/Web-Karma) 工具可以使用本体对数据进行标注，但 Karma 也存在以下两点不足：

- 只能标注单表数据，不能标注多表数据；
- 使用 SQL 导入多表需要建立 JOIN 关系，容易产生大量冗余数据。

因此，我们需要开发一种支持多表标注且冗余数据量小的多表标注算法。

## 介绍

Multi-table to Network (MT2N) 输入 Karma 导出的 RDF 文件，输出 JSON 格式的图。

MT2N 支持以下功能：

- 实体类型和表的对应关系可以是一对一、一对多或多对一。即每张表中可以存在多个实体类型，每个实体类型可以存在于多张表内。
- 更加灵活的实体整合方式。相较于 SQL 严格的主外码关系，MT2N 没有严格的主外键关系。
- 低冗余数据。MT2N 的结果是一张图网络，这种存储方式比表格具有更少的冗余数据，且利于分析。

## 输入

1. TTL 文件所在路径

   每行一个 TTL 文件路径，格式如下：

   ```
   example/msu_data.ttl
   example/msu_data_2.ttl
   example/rap_data.ttl
   ```

2. 实体标识符文件

   每行一个类名和数据属性名，`\t` 分隔，表示指定类通过指定数据属性判断是否为同一个实体，格式如下：

   ```
   <http://www.semanticweb.org/zhang/ontologies/2021/ExampleOntology#Gene>	<http://www.semanticweb.org/zhang/ontologies/2021/ExampleOntology#MSU_ID>
   ```

3. 公共本体路径

   每行一个公共本体名和公共本体路径，`\t` 分隔，格式如下：

   ```
   GO	public_onto/go.owl
   ```

## 输出

1. 图网络 JSON 文件

   格式如下：

   ```json
   {
        "Vertices": [
            {
                "id": 0,
                "entity_type": 0,
                "properties": {
                    "<http://www.w3.org/2000/01/rdf-schema#label>": "9b3afe4c68a6"
                }
            },
            {
                "id": 1,
                "entity_type": 2,
                "properties": {
                    "<http://erlangen-crm.org/current/P82_at_some_time_within>": "1988",
                    "<http://www.w3.org/2000/01/rdf-schema#label>": "Gouache and casein on paper"
                }
            }
       ],
        "Edges": [
            {
                "source_id": 0,
                "target_id": 1,
                "relationship": 0
            }
        ]
   }
   ```
   
2. 实体与实体编号的对应文件
   
   格式如下：
   
   ```
   0	Gene
   1	Go_classification
   ```

3. 关系与关系编号的对应文件

   格式如下：
   
   ```
   0	PartOf
   1	PublicOntoMapping
   ```

4. 用于 Gephi 可视化的 CSV 文件

   结点和边各一个文件。

