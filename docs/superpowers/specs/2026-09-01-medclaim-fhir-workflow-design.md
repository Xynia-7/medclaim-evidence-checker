# MedClaim FHIR/SMART 工作流映射设计

日期：2026-09-01

## 目标

用一份公开、可讲解的 Markdown 说明：如果将 MedClaim 的证据审核方法迁移到 EHR 内的临床文档质量检查，FHIR 资源、SMART 授权、人工复核和审计分别处于什么位置。该材料用于证明临床信息学理解，不声称已经接入或部署 EHR。

## 方案选择

采用“一页只读工作流映射”，不做术语堆砌，也不构建假 SMART 应用。没有真实 EHR 沙箱、组织权限策略和安全评审时，可运行应用不会增加可信证据。

## 范围

- 当前已实现：公开来源主张审核、检索、四分类、Rubric 和人工复核设计。
- 仅作未来概念映射：EHR launch、患者上下文、FHIR 文档读取和审计记录。
- 不处理真实患者数据，不写回临床记录，不生成诊疗建议，不自动发布。

## 数据与权限映射

| 需要 | FHIR/SMART 概念 | 设计约束 |
|---|---|---|
| EHR 内启动 | `iss`、`launch`、授权码和访问令牌 | 由 EHR 授权服务器决定是否授权 |
| 当前患者上下文 | SMART launch context | 上下文不是用户自由输入的患者身份 |
| 临床文档索引 | `DocumentReference` | 只表示文档引用，不等同于结构化事实 |
| 文档组合 | `Bundle` + `Composition` | 保留文档作者、语境与证明关系 |
| 审核来源 | `Provenance` | 描述资源如何产生及涉及的主体 |
| 访问审计 | `AuditEvent` | 记录安全相关事件；与 Provenance 目的不同 |

最小权限只读：按用例请求具体资源的 `.r`/`.rs` scope，不申请通配写权限。任何未来实现都必须使用 PKCE、验证 `state`、TLS 传输并按组织政策管理令牌。

## 概念数据流

EHR 启动并授权 → 获取患者/就诊上下文 → 只读取得相关 `DocumentReference` 或文档 `Bundle` → 在原始上下文内抽取待核主张 → MedClaim 检索与判断 → 人工确认或升级 → 记录模型版本、证据和人工决定。当前设计不包含 FHIR 写回。

## 公开交付

新增 `medclaim-fhir-workflow.md`，包括：

1. Mermaid 工作流；
2. FHIR 资源与 MedClaim 字段映射；
3. SMART 最小授权流程；
4. 五个失败/升级条件；
5. 90 分钟个人验收；
6. 当前事实、未来假设和不可声称内容。

README 只增加一个链接；学习报告只更新完成状态与剩余时数。

## 验收

- 所有技术定义链接到 HL7、SMART Health IT 或澳大利亚数字健康署官方资料；
- 明确 `DocumentReference`、`Provenance`、`AuditEvent` 的不同职责；
- 明确 SMART 授权不替代 EHR 原有权限政策；
- 没有患者数据、令牌、EHR 凭据或部署声明；
- 读者能在 90 秒内讲清“FHIR 是数据模型，SMART 是授权与启动层，MedClaim 是应用逻辑”。
