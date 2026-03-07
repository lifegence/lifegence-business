# Copyright (c) 2025, Lifegence and contributors
# For license information, please see license.txt

"""Gemini classification prompts for committee report analysis."""

from lifegence_compliance.classification.taxonomy import format_taxonomy_for_prompt

SYSTEM_PROMPT = """あなたは日本の第三者委員会報告書の分析専門家です。
報告書のテキストを分析し、3層の分類体系に基づいて構造化された分類結果を返してください。

分類体系:
{taxonomy}

分析の注意点:
- 報告書の内容に基づいて、該当するカテゴリを全て選択してください
- 各カテゴリの確信度を0.0〜1.0で示してください
- 判断の根拠となるテキストを引用してください
- 該当しないカテゴリは含めないでください
- Layer Cは組織文化の特徴であり、報告書から読み取れる組織の文化的問題を分析してください"""


ANALYSIS_PROMPT = """以下の第三者委員会報告書のテキストを分析してください。

---
{text}
---

上記の分類体系に基づき、以下のJSON形式で回答してください。
必ず有効なJSONのみを返してください。説明文は不要です。

{{
  "layer_a": [
    {{"code": "A01", "name": "会計不正・粉飾決算", "confidence": 0.95, "evidence": "根拠テキスト"}}
  ],
  "layer_b": [
    {{"code": "B01", "name": "監査機能不全", "confidence": 0.90, "evidence": "根拠テキスト"}}
  ],
  "layer_c": [
    {{"code": "C01", "name": "同調圧力", "confidence": 0.85, "evidence": "根拠テキスト"}}
  ],
  "summary": "この報告書の概要分析（日本語で2-3文）"
}}"""


CHUNK_ANALYSIS_PROMPT = """以下は第三者委員会報告書の一部です。この部分から読み取れる分類情報を抽出してください。

---
{text}
---

以下のJSON形式で回答してください。該当するカテゴリのみを含めてください。
必ず有効なJSONのみを返してください。

{{
  "layer_a": [
    {{"code": "A01", "confidence": 0.9, "evidence": "根拠テキスト"}}
  ],
  "layer_b": [
    {{"code": "B01", "confidence": 0.8, "evidence": "根拠テキスト"}}
  ],
  "layer_c": [
    {{"code": "C01", "confidence": 0.7, "evidence": "根拠テキスト"}}
  ]
}}"""


def get_system_prompt():
	"""Build the system prompt with taxonomy."""
	taxonomy = format_taxonomy_for_prompt()
	return SYSTEM_PROMPT.format(taxonomy=taxonomy)


def get_analysis_prompt(text, max_length=8000):
	"""Build the analysis prompt for a report text."""
	if len(text) > max_length:
		text = text[:max_length] + "\n...(以下省略)"
	return ANALYSIS_PROMPT.format(text=text)


def get_chunk_analysis_prompt(text, max_length=4000):
	"""Build the analysis prompt for a single chunk."""
	if len(text) > max_length:
		text = text[:max_length] + "\n...(以下省略)"
	return CHUNK_ANALYSIS_PROMPT.format(text=text)
