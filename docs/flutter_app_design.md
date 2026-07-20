# Flutter App 端设计文档 — 学习平台

## 一、架构概览

### 1.1 技术栈

- **网络层**: HTTP POST + JSON，统一请求格式 `{"header": {...}, "body": {...}}`
- **认证**: MD5 签名 + Bearer Token
- **状态管理**: Provider / Riverpod
- **路由**: GoRouter

### 1.2 统一请求格式

```json
{
  "header": {
    "clientId": "app_client_id",
    "X-Token": "access_token",
    // 登录后必传，登录/刷新时传 ""
    "X-Timestamp": "1720000000000",
    // 毫秒时间戳
    "X-Nonce": "random-uuid",
    // 随机 UUID 防重放
    "X-Sign": "md5_hash"
    // MD5(ts+nonce+token+bodyJSON+appSecret)
  },
  "body": {
    /* 业务参数 */
  }
}
```

### 1.3 统一响应格式

```json
{
  "success": true,
  "message": "ok",
  "data": {
    /* 业务数据 */
  }
}
```

### 1.4 业务数据层级链（核心概念）

```
分类(Category) → 阶段(Stage) → 年级(Class) → 地区(Region)
  → 版本(Version) → 年份(Year) → 学期(Semester) → 科目(Subject)
    ↓ 组合成
  Selector（选择器，唯一编码定位一个学习场景）
    ↓ 绑定
  SubjectProfile（过程模板）
    ↓ 包含多个
  Process（学习过程，如"单词基础"、"默写专项"、"拼读练习"）
    ↓ 每个 Process 下挂
  Group（内容组，如"Unit 1 单词学习"）
    ↓ 分
  Section（章节，如"单词卡片"、"单词默写"）
    ↓ 编排
  Line（条目，引用具体数据：单词/题目/媒体/图文）
```

---

## 二、API 接口清单

### 2.1 认证模块 (`/api/v1/auth/`)

| 接口                                  | 用途         | 必填参数                             |
|-------------------------------------|------------|----------------------------------|
| `POST /api/v1/auth/token`           | 登录获取 Token | username, password, tenant(可选)   |
| `POST /api/v1/auth/refresh`         | 刷新 Token   | refresh_token                    |
| `POST /api/v1/auth/revoke`          | 撤销 Token   | token                            |
| `POST /api/v1/auth/userinfo`        | 获取用户信息     | 无                                |
| `POST /api/v1/auth/logout`          | 登出         | 无                                |
| `POST /api/v1/auth/change-password` | 修改密码       | old_password, new_password(>=6位) |

### 2.2 导航模块 (`/api/v1/learn/`)

| 接口                                       | 用途              | 参数                                               |
|------------------------------------------|-----------------|--------------------------------------------------|
| `POST /api/v1/learn/nav_tabs`            | 底部导航 Tab 列表     | 无                                                |
| `POST /api/v1/learn/home_subcategories`  | 首页分类聚合          | category_code(可选)                                |
| `POST /api/v1/learn/tab_selector`        | 维度选择器树          | category_code, sub_category_code                 |
| `POST /api/v1/learn/profiles`            | 全部 Profile 模板列表 | 无                                                |
| `POST /api/v1/learn/profile`             | 单个 Profile      | selector_code                                    |
| `POST /api/v1/learn/selector_processes`  | 选择器下过程列表+内容组    | selector_code, page_num, page_size               |
| `POST /api/v1/learn/groups`              | 内容组列表           | selector_code, process_code, page_num, page_size |
| `POST /api/v1/learn/group/{id}/sections` | 内容组章节+条目详情      | URL: group_id                                    |
| `POST /api/v1/learn/content_types`       | 所有内容类型          | 无                                                |
| `POST /api/v1/learn/search`              | 全局搜索            | keyword, scope(可选)                               |

---

## 三、Flutter 数据模型 (Dart)

```dart
// ========== 基础类型 ==========

class DimNode {
  final int id;
  final String code;
  final String name;
  final int sequence;
  final String dimType;
  final String dimDesc;
  final List<DimNode> children;
  final String? selectorCode; // 仅 subject 节点有
}

class ProcessInfo {
  final int id;
  final String name;
  final String code;
  final int sequence;
}

class ProfileInfo {
  final int id;
  final String name;
  final String description;
  final List<ProcessInfo> processes;
}

class ContentTypeInfo {
  final int id;
  final String name;
  final String code;
  final String storageModel; // learn.phrase / learn.question / learn.media / learn.article
  final bool hasScore;
  final int sequence;
  final String description;
}

class GroupItem {
  final int id;
  final String name;
  final int sequence;
  final String description;
  final int sectionCount;
  final int itemCount;
}

class SectionInfo {
  final int id;
  final String name;
  final int sequence;
  final String contentType;
  final double score;
  final List<SectionLine> lines;
}

class SectionLine {
  final int id;
  final int sequence;
  final String contentType;
  final double score;
  // 根据 contentType/storageModel 填充以下之一:
  final WordInfo? word;
  final CharacterInfo? character;
  final PhraseInfo? phrase;
  final QuestionInfo? question;
  final MediaInfo? media;
  final ArticleInfo? article;
}

// ========== 知识库原子数据 ==========

class WordInfo {
  final int id;
  final String name;        // 单词
  final String phonetic;    // 音标
  final String meaning;     // 中文释义
  final String meaningEn;   // 英文释义
  final String exampleSentence;
  final String phrases;     // 关联短语
  final String difficulty;  // easy/medium/hard
  final List<PosInfo> pos;  // 词性
}

class CharacterInfo {
  final int id;
  final String name;     // 生字
  final String pinyin;
  final int strokes;
  final String radical;
  final String meaning;
  final String phrases;  // 组词
  final String difficulty;
}

class PhraseInfo {
  final int id;
  final String name;
  final String phraseType; // word_card/word_dictation/word_phonics/char_dictation...
  final String refModel;   // learn.word / learn.character
  final WordInfo? word;    // 展开的单词数据
  final CharacterInfo? character; // 展开的生字数据
}

class QuestionInfo {
  final int id;
  final String questionType; // single_choice/multi_choice/fill_blank/true_false/calculation/essay
  final String stem;         // 题干 (HTML)
  final String? stemImage;   // 题干图片 (base64)
  final Map<String, String> options; // {A, B, C, D, E, F}
  final double score;
  final String difficulty;
  // 答案通过单独接口获取
}

class MediaInfo {
  final int id;
  final String name;
  final String mediaType; // video/audio/file
  final String url;
  final String fileName;
  final int duration; // 秒
}

class ArticleInfo {
  final int id;
  final String name;
  final String articleType; // knowledge/poem_recite
  final String content;     // HTML 正文
  final String tags;
}

class PosInfo {
  final int id;
  final String name;
  final String code;
}

// ========== 搜索结果 ==========

class SearchData {
  final String keyword;
  final SearchResults results;
}

class SearchResults {
  final List<WordResult>? words;
  final List<CharacterResult>? characters;
  final List<QuestionResult>? questions;
}

class WordResult {
  final int id;
  final String name;
  final String phonetic;
  final String meaning;
  final String difficulty;
  final List<PosInfo> pos;
}

class CharacterResult {
  final int id;
  final String name;
  final String pinyin;
  final String meaning;
  final int strokes;
  final String radical;
  final String difficulty;
}

class QuestionResult {
  final int id;
  final String questionType;
  final String stem;
  final String difficulty;
}
```

---

## 四、页面路由设计

```
/                          → SplashPage（启动页）
/login                     → LoginPage（登录）
/main                      → MainPage（主页，含底部导航）
  Tab 0: /main/home        → HomePage（首页，分类+阶段入口）
  Tab 1: /main/subject     → SubjectPage（科目学习页）
  Tab 2: /main/profile     → ProfilePage（个人中心）
/selector                  → SelectorPage（维度选择器，多级筛选）
/learning                  → LearningPage（学习主页）
  /learning/process/{code} → ProcessListPage（过程列表）
  /learning/group/{id}     → GroupPage（内容组详情，含章节）
  /learning/group/{id}/section/{sectionId}
                            → SectionPage（单个章节学习）
/learn/word-card           → WordCardPage（单词卡片学习）
/learn/word-dictation      → WordDictationPage（单词默写）
/learn/word-phonics        → WordPhonicsPage（单词拼读）
/learn/char-dictation      → CharDictationPage（生字词默写）
/learn/char-phonics        → CharPhonicsPage（生字拼读）
/learn/char-group          → CharGroupPage（生字组词）
/learn/single-choice       → SingleChoicePage（单选题）
/learn/multi-choice        → MultiChoicePage（多选题）
/learn/fill-blank          → FillBlankPage（填空题）
/learn/true-false          → TrueFalsePage（判断题）
/learn/calculation         → CalculationPage（计算题）
/learn/essay               → EssayPage（问答题）
/learn/video               → VideoPage（视频播放）
/learn/audio               → AudioPage（音频播放）
/learn/file                → FilePage（资料下载）
/learn/knowledge           → KnowledgePage（知识要点阅读）
/learn/poem-recite         → PoemRecitePage（诗词背诵）
/search                    → SearchPage（全局搜索）
```

---

## 五、页面流程

### 5.1 启动 → 首页 → 选择学习内容

```
SplashPage
  ├─ 检查本地 Token
  │   ├─ 有 Token → 调用 refresh 刷新 → 进入 MainPage
  │   └─ 无 Token → LoginPage
  │       └─ 调用 token 登录 → 保存 Token → MainPage
  │
MainPage（底部 3 个 Tab）
  ├─ Tab: 首页
  │   └─ 调用 nav_tabs 获取分类列表
  │       └─ 点击分类 → 调用 home_subcategories(category_code)
  │           └─ 显示阶段列表 → 点击阶段
  │               └─ 跳转 SelectorPage(category_code, stage_code)
  │
  ├─ Tab: 学习
  │   └─ 显示最近学习记录（TODO）
  │   └─ 或直接跳 SelectorPage
  │
  └─ Tab: 我的
      └─ 用户信息、收藏、错题本、设置
```

### 5.2 维度选择器 → 过程 → 内容组

```
SelectorPage
  ├─ 调用 tab_selector(category_code?, sub_category_code?)
  │   返回: {default_condition, conditions}（递归维度树）
  │
  ├─ 显示多级级联选择器
  │   Level 1: 年级 (class)
  │   Level 2: 地区 (region)
  │   Level 3: 版本 (version)
  │   Level 4: 年份 (year)
  │   Level 5: 学期 (semester)
  │   Level 6: 科目 (subject) → 此处带 selector_code
  │
  └─ 选中 subject → 拿到 selector_code
      └─ 调用 selector_processes(selector_code)
          返回: [{process_id, process_name, process_code, sequence, groups}]
          │
          ├─ 第一个过程自动展开内容组列表
          │   └─ 点击内容组 → GroupPage(group_id)
          │
          └─ 切换过程 Tab → 调用 groups(selector_code, process_code)
              └─ 返回分页内容组列表
```

### 5.3 内容组 → 章节 → 学习

```
GroupPage(group_id)
  └─ 调用 group/{id}/sections
      返回: [
        {
          id, name, sequence, content_type, score,
          lines: [{...具体数据...}]
        }
      ]
      │
      ├─ 按 section 展示学习模块列表
      │   Section 1: "单词卡片" (content_type=word_card)
      │   Section 2: "单词默写" (content_type=word_dictation)
      │   Section 3: "单选题" (content_type=single_choice)
      │   ...
      │
      └─ 点击 Section → 进入对应学习页面
          ├─ word_card → WordCardPage(section)
          ├─ word_dictation → WordDictationPage(section)
          ├─ word_phonics → WordPhonicsPage(section)
          ├─ single_choice → SingleChoicePage(section)
          └─ ...
```

---

## 六、学习交互设计

### 6.1 单词卡片 (content_type = word_card)

**功能**: 翻转卡片查看单词的音标、释义、例句、词性。

**数据来源**: `SectionLine.phrase.word`（通过 phrase 桥接层展开的 WordInfo）

**UI 设计**:

- 卡片正面：单词 + 音标
- 卡片反面：中文释义 + 例句 + 词性标签
- 左右滑动切换下一个单词
- 顶部进度条（当前第 N 个/共 M 个）
- 底部按钮：认识 / 不认识（记录学习状态）
- 右上角：发音按钮（播放 audio_file，如果后端有提供）

**状态管理**:

```dart
class WordCardState {
  final List<WordInfo> words;
  int currentIndex;
  Set<int> knownWords;     // 已认识的单词 index
  Set<int> unknownWords;   // 不认识的单词 index
  bool isFlipped;
}
```

### 6.2 单词默写 (content_type = word_dictation)

**功能**: 听发音写单词，或看中文写英文。

**数据来源**: `SectionLine.phrase.word`

**UI 设计**:

- 模式 1（听写）：播放发音 → 输入框输入单词 → 提交对比
- 模式 2（中译英）：显示中文释义 → 输入英文单词 → 提交对比
- 答对：绿色对勾 + 自动下一题
- 答错：红色叉号 + 显示正确答案 + 手动点下一题
- 底部：进度条 + 正确率

**评分**: 每题 score 分，全对满分。

### 6.3 单词拼读 (content_type = word_phonics)

**功能**: 跟读发音，语音评测。

**数据来源**: `SectionLine.phrase.word`

**UI 设计**:

- 显示单词 + 音标 + 释义
- 播放标准发音（audio_file）
- 用户点击录音按钮跟读
- 调用语音识别/评测 API（需集成第三方 SDK，如讯飞/腾讯云）
- 显示评测结果：发音准确度百分比、音素级评分
- 左右滑动下一词

### 6.4 生字词默写 (content_type = char_dictation)

**功能**: 看释义默写生字/词语。

**数据来源**: `SectionLine.phrase.character`（通过 phrase 桥接到 CharacterInfo）

**UI 设计**:

- 显示释义 + 拼音提示（可选）
- 手写输入区域（Canvas 或 手写键盘）
- 提交后 OCR/笔画识别对比
- 显示正确写法（含笔顺动画）

### 6.5 生字拼读 (content_type = char_phonics)

**功能**: 生字跟读发音评测。

**数据来源**: `SectionLine.phrase.character`

**UI 设计**: 同单词拼读，但显示拼音 + 部首 + 笔画

### 6.6 生字组词 (content_type = char_group)

**功能**: 生字组词练习。

**数据来源**: `SectionLine.phrase.character`

**UI 设计**:

- 显示生字
- 多个输入框用于填写组词
- 提交后与 character.phrases 对比
- 显示标准组词列表

### 6.7 选择题 (content_type = single_choice / multi_choice)

**功能**: 单选/多选答题。

**数据来源**: `SectionLine.question`

**UI 设计**:

- 显示题干（支持 HTML 渲染，如 flutter_html）
- 显示选项列表（单选圆形 radio，多选方形 checkbox）
- 提交后显示对错 + 答案解析
- 底部：进度 + 已得分/总分

**注意**: 题目列表不含答案，答案需单独从后端获取（或通过考试接口提交后获取）。

### 6.8 填空题 (content_type = fill_blank)

**数据来源**: `SectionLine.question`

**UI 设计**:

- 显示题干（含 ___ 占位符）
- 输入框填空
- 提交对比正确答案

### 6.9 判断题 (content_type = true_false)

**数据来源**: `SectionLine.question`

**UI 设计**:

- 显示题干
- 两个大按钮：✓ 正确 / ✗ 错误
- 提交显示对错

### 6.10 计算题 (content_type = calculation)

**数据来源**: `SectionLine.question`

**UI 设计**:

- 显示题干
- 数字键盘输入答案
- 提交对比

### 6.11 问答题 (content_type = essay)

**数据来源**: `SectionLine.question`

**UI 设计**:

- 显示题干
- 多行文本输入框
- 提交后显示参考答案（人工对比，不自动评分）

### 6.12 视频/音频 (content_type = video / audio)

**数据来源**: `SectionLine.media`

**UI 设计**:

- 使用 video_player / audioplayers 插件播放
- 显示标题、时长
- 进度条、播放/暂停控制

### 6.13 资料下载 (content_type = file)

**数据来源**: `SectionLine.media`

**UI 设计**:

- 显示文件名、大小
- 下载按钮 → 调用 open_file 打开

### 6.14 知识要点 (content_type = knowledge)

**数据来源**: `SectionLine.article`

**UI 设计**:

- 渲染 HTML 正文（flutter_html）
- 支持图片、表格、富文本

### 6.15 诗词背诵 (content_type = poem_recite)

**数据来源**: `SectionLine.article`

**UI 设计**:

- 原文展示
- 译文/注释展开
- 背诵模式：隐藏原文，用户输入背诵，对比

---

## 七、学习页面通用 Widget 架构

```dart
// 学习页面基类
abstract class LearnPage extends StatefulWidget {
  final SectionInfo section;
  int currentIndex = 0;
  int correctCount = 0;
  int wrongCount = 0;
  
  void onCorrect();   // 答对回调
  void onWrong();     // 答错回调
  void onNext();      // 下一题
  void onFinish();    // 完成回调
  Widget buildContent(int index); // 子类实现具体学习 UI
}

// 每种内容类型对应一个 LearnPage 子类:
// WordCardPage, WordDictationPage, WordPhonicsPage,
// SingleChoicePage, FillBlankPage, ...
```

**Widget 工厂**:

```dart
Widget buildLearnPage(SectionInfo section) {
  switch (section.contentType) {
    case 'word_card': return WordCardPage(section: section);
    case 'word_dictation': return WordDictationPage(section: section);
    case 'word_phonics': return WordPhonicsPage(section: section);
    case 'char_dictation': return CharDictationPage(section: section);
    case 'char_phonics': return CharPhonicsPage(section: section);
    case 'char_group': return CharGroupPage(section: section);
    case 'single_choice': return SingleChoicePage(section: section);
    case 'multi_choice': return MultiChoicePage(section: section);
    case 'fill_blank': return FillBlankPage(section: section);
    case 'true_false': return TrueFalsePage(section: section);
    case 'calculation': return CalculationPage(section: section);
    case 'essay': return EssayPage(section: section);
    case 'video': return VideoPage(section: section);
    case 'audio': return AudioPage(section: section);
    case 'file': return FilePage(section: section);
    case 'knowledge': return KnowledgePage(section: section);
    case 'poem_recite': return PoemRecitePage(section: section);
    default: return UnsupportedPage(section: section);
  }
}
```

---

## 八、API 调用服务层

```dart
class ApiService {
  static const baseUrl = 'https://your-odoo-server.com';
  
  // 统一请求方法
  Future<Map<String, dynamic>> _post(String path, Map<String, dynamic> body) async {
    final header = _buildHeader(body);
    final response = await http.post(
      Uri.parse('$baseUrl$path'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'header': header, 'body': body}),
    );
    final data = jsonDecode(response.body);
    if (data['success'] != true) throw ApiException(data['message']);
    return data;
  }

  // ========== 认证 ==========
  Future<TokenData> login(String username, String password, {String? tenant});
  Future<TokenData> refreshToken(String refreshToken);
  Future<void> logout();
  Future<UserInfo> getUserInfo();

  // ========== 导航 ==========
  Future<List<NavTab>> getNavTabs();
  Future<List<HomeCategoryGroup>> getHomeSubcategories({String? categoryCode});
  Future<TabSelectorData> getTabSelector({String? categoryCode, String? subCategoryCode});

  // ========== 学习 ==========
  Future<List<ProfileInfo>> getProfiles();
  Future<ProfileInfo> getProfile(String selectorCode);
  Future<List<SelectorProcessItem>> getSelectorProcesses(String selectorCode, {int page, int pageSize});
  Future<GroupListData> getGroups(String selectorCode, String processCode, {int page, int pageSize});
  Future<List<SectionInfo>> getGroupSections(int groupId);
  Future<List<ContentTypeInfo>> getContentTypes();

  // ========== 搜索 ==========
  Future<SearchData> search(String keyword, {String scope = 'all', int pageSize = 20});
}
```

---

## 九、开发优先级

### Phase 1 — 基础框架

1. 登录/Token 管理
2. 底部导航 + 首页分类展示
3. 维度选择器（多级级联）
4. 过程列表 + 内容组列表

### Phase 2 — 核心学习

1. 内容组章节展示
2. 单词卡片（word_card）
3. 单词默写（word_dictation）
4. 选择题（single_choice / multi_choice）

### Phase 3 — 扩展学习

1. 单词拼读（word_phonics）
2. 生字相关（char_dictation / char_phonics / char_group）
3. 填空题、判断题、计算题、问答题
4. 视频/音频/图文/诗词

### Phase 4 — 辅助功能

1. 全局搜索
2. 收藏、错题本
3. 学习记录/进度统计
4. 离线缓存

---

## 十、App 生命周期管理

### 10.1 模块概述

App 生命周期管理负责移动端 App 的版本更新、插件更新、素材更新、渠道和终端管控。App 冷启动或登录时调用综合校验接口，一次性获取所有更新信息。

**后端模块**: `app_manage_core` + `app_manage_api`
**API 前缀**: `/api/v1/app/check/`

### 10.2 数据模型 (Dart)

```dart
// ========== 版本更新 ==========

class VersionCheckInfo {
  final bool forceUpdate;
  final bool needUpdate;
  final String? latestVersion;
  final int? latestVersionCode;
  final String? minSupportVersion;
  final String? updateUrl;
  final String releaseNote;
  final int? packageSize;
  final String? baselineName;
  final String? message;
}

// ========== 插件更新 ==========

class PluginUpdateInfo {
  final String pluginCode;
  final String? pluginName;
  final int currentVersionCode;
  final int? latestVersionCode;
  final String? latestVersion;
  final bool needsUpdate;
  final bool forceUpdate;
  final String? distributionMode; // "mandatory" | "optional" | "silent"
  final bool requireRestart;
  final String? downloadUrl;
  final String? releaseNote;
  final int? packageSize;
}

// ========== 素材资源 ==========

class ResourceInfo {
  final int id;
  final String name;
  final String resourceType;
  final String? onlineUrl;
  final String? resolution;
  final String? density;
  final int? fileSize;
  final bool forceUpdate;
  final int? updateIntervalHours;
}

// ========== 校验结果 ==========

class CheckResult {
  final bool allowed;
  final String message;
}

// ========== 综合校验响应（check/login 接口返回） ==========

class LoginCheckData {
  final bool forceUpdate;
  final bool needUpdate;
  final String? latestVersion;
  final int? latestVersionCode;
  final String? updateUrl;
  final String releaseNote;
  final bool terminalAllowed;
  final String terminalMessage;
  final bool channelAllowed;
  final String channelMessage;
  final List<PluginUpdateInfo> plugins;
  final List<ResourceInfo> resources;
}
```

### 10.3 API 接口清单

| 接口 | 用途 | 必填参数 |
|------|------|---------|
| `POST /api/v1/app/check/login` | **综合校验**（一次性返回版本+插件+素材+终端+渠道） | app_version_code, platform |
| `POST /api/v1/app/check/version` | 单独检查版本更新 | app_version_code, platform |
| `POST /api/v1/app/check/plugins` | 单独检查插件更新 | platform, installed_plugins |
| `POST /api/v1/app/check/resources` | 单独检查素材更新 | platform, app_version_code |
| `POST /api/v1/app/check/terminal` | 单独校验终端白名单 | platform, terminal_model |
| `POST /api/v1/app/check/channel` | 单独校验渠道白名单 | channel_code, user_id(可选) |

### 10.4 核心接口详解

#### 10.4.1 `POST /api/v1/app/check/login` — 综合校验

App 冷启动或用户登录时调用，一次性返回所有校验结果，减少网络请求次数。

**Request Body**:
```json
{
  "header": { "clientId": "xxx", "X-Token": "xxx", ... },
  "body": {
    "app_version": "1.0.0",
    "app_version_code": 1000,
    "platform": "android",
    "platform_version": "14",
    "terminal_model": "SM-S9280",
    "channel_code": "huawei",
    "user_id": 1,
    "installed_plugins": [
      {"plugin_code": "ocr", "version_code": 100},
      {"plugin_code": "push", "version_code": 200}
    ]
  }
}
```

**Response Body**:
```json
{
  "success": true,
  "data": {
    "force_update": false,
    "need_update": true,
    "latest_version": "1.2.0",
    "latest_version_code": 1200,
    "update_url": "https://cdn.example.com/app_v1.2.0.apk",
    "release_note": "修复若干已知问题，优化性能",
    "terminal_allowed": true,
    "terminal_message": "OK",
    "channel_allowed": true,
    "channel_message": "OK",
    "plugins": [
      {
        "plugin_code": "ocr",
        "plugin_name": "OCR 识别插件",
        "current_version_code": 100,
        "latest_version_code": 150,
        "latest_version": "1.5.0",
        "needs_update": true,
        "force_update": false,
        "distribution_mode": "optional",
        "require_restart": false,
        "download_url": "https://cdn.example.com/plugins/ocr_v1.5.0.zip",
        "release_note": "提升识别准确率",
        "package_size": 2048000
      }
    ],
    "resources": [
      {
        "id": 1,
        "name": "app_icon_set",
        "resource_type": "image",
        "online_url": "https://cdn.example.com/resources/icons.zip",
        "resolution": "1080x2400",
        "density": "xxhdpi",
        "file_size": 512000,
        "force_update": false,
        "update_interval_hours": 24
      }
    ]
  }
}
```

### 10.5 App 启动流程

```
App 冷启动 / 用户登录
  │
  ├─ 1. 调用 check/login（综合校验）
  │     ├─ 返回 force_update=true → 强制更新弹窗（不可跳过）
  │     │   └─ 用户点击更新 → 跳转应用商店 / 下载 APK
  │     │
  │     ├─ 返回 need_update=true → 提示更新弹窗（可跳过）
  │     │   └─ 用户点击更新 → 后台下载 → 安装
  │     │
  │     ├─ terminal_allowed=false → 提示设备不支持，退出
  │     ├─ channel_allowed=false → 提示渠道不可用，退出
  │     │
  │     ├─ plugins 中有 needs_update=true 的插件
  │     │   ├─ force_update=true → 强制更新插件（阻塞）
  │     │   └─ force_update=false → 后台静默下载
  │     │
  │     └─ resources 中有需要更新的素材
  │         └─ 检查本地缓存时间 > update_interval_hours → 下载更新
  │
  └─ 2. 校验通过 → 进入 MainPage
```

### 10.6 更新策略实现

```dart
class AppUpdateService {
  final ApiService _api;

  /// 综合校验（冷启动时调用）
  Future<LoginCheckData> checkOnStartup({
    required int appVersionCode,
    required String platform,
    String? platformVersion,
    String? terminalModel,
    String? channelCode,
    int? userId,
    List<Map<String, dynamic>>? installedPlugins,
  }) async {
    final body = {
      'app_version_code': appVersionCode,
      'platform': platform,
      if (platformVersion != null) 'platform_version': platformVersion,
      if (terminalModel != null) 'terminal_model': terminalModel,
      if (channelCode != null) 'channel_code': channelCode,
      if (userId != null) 'user_id': userId,
      if (installedPlugins != null) 'installed_plugins': installedPlugins,
    };
    final res = await _api._post('/api/v1/app/check/login', body);
    return LoginCheckData.fromJson(res['data']);
  }

  /// 处理启动校验结果
  Future<StartupCheckResult> handleStartupCheck(LoginCheckData data) async {
    // 1. 强制更新
    if (data.forceUpdate) {
      return StartupCheckResult.forceUpdate(data);
    }
    // 2. 终端/渠道校验
    if (!data.terminalAllowed) {
      return StartupCheckResult.blocked(data.terminalMessage);
    }
    if (!data.channelAllowed) {
      return StartupCheckResult.blocked(data.channelMessage);
    }
    // 3. 可选更新
    if (data.needUpdate) {
      _showOptionalUpdateDialog(data);
    }
    // 4. 插件更新
    for (final plugin in data.plugins) {
      if (plugin.forceUpdate) {
        await _downloadPlugin(plugin);
      } else if (plugin.needsUpdate) {
        _schedulePluginDownload(plugin);
      }
    }
    // 5. 素材更新
    _checkResourceUpdates(data.resources);
    
    return StartupCheckResult.passed();
  }

  Future<void> _downloadPlugin(PluginUpdateInfo plugin) async { ... }
  void _schedulePluginDownload(PluginUpdateInfo plugin) { ... }
  void _checkResourceUpdates(List<ResourceInfo> resources) { ... }
}

enum StartupCheckStatus { passed, forceUpdate, blocked }

class StartupCheckResult {
  final StartupCheckStatus status;
  final String? message;
  final VersionCheckInfo? versionInfo;
}
```

### 10.7 版本更新 UI

```
┌─────────────────────────────────┐
│  🔔 发现新版本                    │
│                                 │
│  最新版本：1.2.0                  │
│  当前版本：1.0.0                  │
│                                 │
│  更新内容：                       │
│  · 修复若干已知问题                │
│  · 优化性能                       │
│  · 新增 XX 功能                   │
│                                 │
│  包大小：25.6 MB                  │
│                                 │
│  ┌─────────────────────────┐    │
│  │      立即更新 (force)      │    │
│  └─────────────────────────┘    │
│  ┌─────────────────────────┐    │
│  │      稍后再说 (optional)   │    │
│  └─────────────────────────┘    │
└─────────────────────────────────┘
```

**强制更新**：只显示"立即更新"按钮，不可关闭弹窗。
**可选更新**：显示"立即更新" + "稍后再说"，可关闭。

### 10.8 插件管理 UI

```
┌─────────────────────────────────┐
│  插件列表                         │
│                                 │
│  ┌─────────────────────────┐    │
│  │ 📦 OCR 识别插件    1.0.0  │    │
│  │ 有新版本 1.5.0   [更新]   │    │
│  └─────────────────────────┘    │
│  ┌─────────────────────────┐    │
│  │ 📦 推送插件        2.0.0  │    │
│  │ 已是最新                    │    │
│  └─────────────────────────┘    │
│  ┌─────────────────────────┐    │
│  │ 📦 地图插件        1.0.0  │    │
│  │ 下载中 45%  [取消]        │    │
│  └─────────────────────────┘    │
└─────────────────────────────────┘
```

**插件状态**：已安装(最新) / 有更新 / 下载中 / 待安装(需重启)

### 10.9 素材管理

素材（图标、启动页、字体等）由后端管理，App 根据 `update_interval_hours` 定期检查更新。

```dart
class ResourceManager {
  /// 检查素材是否需要更新
  Future<void> checkAndDownload(List<ResourceInfo> resources) async {
    for (final res in resources) {
      final lastCheck = _getLastCheckTime(res.id);
      final hoursSinceCheck = DateTime.now().difference(lastCheck).inHours;
      
      if (hoursSinceCheck >= (res.updateIntervalHours ?? 24)) {
        await _downloadResource(res);
        _setLastCheckTime(res.id, DateTime.now());
      }
    }
  }
}
```

### 10.10 路由补充

```
/settings/about             → AboutPage（关于页面，手动检查更新）
/settings/plugins           → PluginManagePage（插件管理列表）
/settings/plugin/{code}     → PluginDetailPage（插件详情）
/update/force               → ForceUpdatePage（强制更新页，不可返回）
/update/optional            → OptionalUpdateDialog（可选更新弹窗）
```

### 10.11 API 服务层补充

```dart
class ApiService {
  // ... 已有方法 ...

  // ========== App 生命周期 ==========
  Future<LoginCheckData> checkLogin({...});
  Future<VersionCheckInfo> checkVersion(int appVersionCode, String platform, {String? platformVersion});
  Future<List<PluginUpdateInfo>> checkPlugins(String platform, List<Map<String, dynamic>> installedPlugins);
  Future<List<ResourceInfo>> checkResources(String platform, int appVersionCode);
  Future<CheckResult> checkTerminal(String platform, String terminalModel);
  Future<CheckResult> checkChannel(String channelCode, {int? userId});
}
```

### 10.12 开发优先级补充

### Phase 0 — App 启动流程（最高优先级）
1. 综合校验接口对接 (check/login)
2. 强制更新弹窗（不可跳过）
3. 可选更新弹窗
4. 插件更新下载管理
5. 素材更新管理
