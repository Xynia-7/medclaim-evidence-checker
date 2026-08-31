# MedClaim Evidence Checker｜首批资料源

核验日期：2026-09-01  
主题：HER2 阳性胃癌/胃食管结合部癌与抗体偶联药物（ADC）医学主张证据审核。

## 资料使用原则

1. 首批知识库只用政府、监管机构、PubMed 摘要及明确开放获取全文；
2. 每条资料记录标题、机构、发布日期/更新日期、URL 和用途；
3. 付费或许可不清的全文不上传到公开知识库；
4. 用户参与发表的论文可作为领域背景和书目信息，但不能因为作者身份默认拥有出版社全文再分发权；
5. 原型不使用真实患者数据，也不提供个体化诊断或治疗建议。

## P0｜首批必须使用

| 来源 | 类型与当前状态 | 用途 | 注意事项 |
|---|---|---|---|
| [NCI Gastric Cancer Treatment PDQ](https://www.cancer.gov/types/stomach/hp/stomach-treatment-pdq) | 美国国家癌症研究所专业版；持续更新 | 胃癌治疗线别、HER2 检测、trastuzumab deruxtecan 的证据概览 | 记录页面复核日期；不要把美国语境自动外推到所有地区 |
| [FDA 2025 ENHERTU Label](https://www.accessdata.fda.gov/drugsatfda_docs/label/2025/761139s038s042lbl.pdf) | 美国药品标签 | 获批适应证、用法、安全性与警示的监管金标准 | 版本为 2025 标签；项目每次展示前检查是否有更新 |
| [FDA Gastric Cancer Approval Notice](https://www.fda.gov/drugs/resources-information-approved-drugs/fda-approves-fam-trastuzumab-deruxtecan-nxki-her2-positive-gastric-adenocarcinomas) | 2021-01-15 批准公告 | 训练“获批事实”和“试验发现”区别 | 批准公告不能替代完整当前标签 |
| [EMA Enhertu EPAR](https://www.ema.europa.eu/en/medicines/human/EPAR/enhertu) | EMA 药品概览；页面显示 2026-07 更新 | 欧盟适应证、获益/风险和监管评估背景 | 与 FDA 标签可能存在地区和版本差异 |
| [EMA Enhertu Product Information](https://www.ema.europa.eu/en/documents/product-information/enhertu-epar-product-information_en.pdf) | 欧盟产品信息 | 人群、HER2 定义、剂量和安全性核对 | 保存下载日期和文档版本 |

## P1｜领域背景与开放文献

| 来源 | 类型 | 用途 | 注意事项 |
|---|---|---|---|
| [用户共同第一作者综述，PMID 38963593](https://pubmed.ncbi.nlm.nih.gov/38963593/) | Gastric Cancer, 2024；综述 | 建立 ADC 机制、靶点和临床策略词表；连接个人经历 | 公开项目优先使用 PubMed 摘要和合法可见部分，不上传版权不明全文 |
| [2026 胃癌 ADC 临床进展与耐药综述，PMID 41484653](https://pubmed.ncbi.nlm.nih.gov/41484653/) | Gastric Cancer, 2026；综述摘要 | 构造“综述判断 vs 已获批事实”案例 | 综述中的早期结果不能写成监管结论 |
| [开放获取 ADC 胃癌综述，PMC11972320](https://pmc.ncbi.nlm.nih.gov/articles/PMC11972320/) | Cell Death Discovery, 2025；CC BY 4.0 全文已核验 | 补充机制、RC48、T-DXd、CMG901、SKB264 与研究阶段，训练段落级检索 | 中文转述保留标题、PMCID、章节、许可和改写说明；二手监管陈述仍回原始来源核验 |
| [2026 Advanced Gastric Cancer Antibodies/ADCs，PMID 42122244](https://pubmed.ncbi.nlm.nih.gov/42122244/) | 2026 开放获取综述 | 检查新近治疗版图和术语 | 与监管标签冲突时，以当前监管资料和指南为准 |

## P2｜第二批再加入

- 关键临床试验的 PubMed 摘要或开放全文；
- 中国 NMPA 可公开获取的说明书/批准信息；
- 其他国家/地区监管标签，用于构造“地区差异”测试；
- 合法开放获取的系统综述与方法学论文。

加入前必须回答：

1. 这份资料解决哪个现有测试缺口？
2. 是否比现有资料更新或更权威？
3. 是否允许被导入公开项目？
4. 它是监管事实、试验结果、综述判断还是探索性发现？

答不出来就不加入，避免知识库变成无边界文献堆。

## 首批 10 条测试分布

| 类型 | 数量 | 示例方向 |
|---|---:|---|
| 支持 | 2 | 当前标签与主张在人群、线别和适应证上完全一致 |
| 部分支持 | 2 | 来源支持疗效方向，但主张扩大了人群或结论强度 |
| 不支持 | 2 | 来源明确与主张矛盾 |
| 证据不足 | 1 | 来源未报告主张涉及的结局 |
| 人群/线别错配 | 2 | 把经 trastuzumab 治疗后的适应证写成一线或未选择人群 |
| 数值失真 | 1 | ORR、样本量、OS 或不良事件数字被错误转述 |

这 10 条先用于人工 Rubric 校准；标准稳定后再扩到 50 条。
