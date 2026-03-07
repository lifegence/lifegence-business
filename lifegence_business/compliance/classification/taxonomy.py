# Copyright (c) 2025, Lifegence and contributors
# For license information, please see license.txt

"""
3-Layer Classification Taxonomy for Third-party Committee Reports.

Layer A: Incident Types (不正類型) - 14 categories
Layer B: Organizational Mechanisms (組織メカニズム) - 15 categories
Layer C: Corporate Culture (組織文化) - 10 categories
"""

LAYER_A = {
	"A01": {"name": "会計不正・粉飾決算", "name_en": "Accounting Fraud"},
	"A02": {"name": "横領・着服", "name_en": "Embezzlement"},
	"A03": {"name": "贈収賄", "name_en": "Bribery"},
	"A04": {"name": "品質偽装", "name_en": "Quality Fraud"},
	"A05": {"name": "データ改ざん", "name_en": "Data Falsification"},
	"A06": {"name": "情報漏洩", "name_en": "Information Leak"},
	"A07": {"name": "ハラスメント", "name_en": "Harassment"},
	"A08": {"name": "独占禁止法違反", "name_en": "Antitrust Violation"},
	"A09": {"name": "インサイダー取引", "name_en": "Insider Trading"},
	"A10": {"name": "利益相反", "name_en": "Conflict of Interest"},
	"A11": {"name": "環境違反", "name_en": "Environmental Violation"},
	"A12": {"name": "労働法違反", "name_en": "Labor Violation"},
	"A13": {"name": "知的財産侵害", "name_en": "IP Infringement"},
	"A14": {"name": "その他", "name_en": "Other Incident"},
}

LAYER_B = {
	"B01": {"name": "監査機能不全", "name_en": "Audit Dysfunction"},
	"B02": {"name": "内部通報制度の問題", "name_en": "Whistleblower Issues"},
	"B03": {"name": "取締役会の監督不足", "name_en": "Board Oversight Failure"},
	"B04": {"name": "リスク管理体制の不備", "name_en": "Risk Management Failure"},
	"B05": {"name": "内部統制の不備", "name_en": "Internal Control Failure"},
	"B06": {"name": "コンプライアンス体制の不備", "name_en": "Compliance Framework Failure"},
	"B07": {"name": "情報開示の不備", "name_en": "Disclosure Failure"},
	"B08": {"name": "人事評価制度の問題", "name_en": "HR Evaluation Issues"},
	"B09": {"name": "教育研修の不足", "name_en": "Training Inadequacy"},
	"B10": {"name": "ITシステムの不備", "name_en": "IT System Failure"},
	"B11": {"name": "子会社管理の不備", "name_en": "Subsidiary Management Failure"},
	"B12": {"name": "外部委託管理の不備", "name_en": "Outsourcing Management Failure"},
	"B13": {"name": "文書管理の不備", "name_en": "Document Management Failure"},
	"B14": {"name": "権限管理の不備", "name_en": "Authority Management Failure"},
	"B15": {"name": "その他", "name_en": "Other Mechanism"},
}

LAYER_C = {
	"C01": {"name": "同調圧力", "name_en": "Conformity Pressure"},
	"C02": {"name": "権威勾配", "name_en": "Authority Gradient"},
	"C03": {"name": "業績至上主義", "name_en": "Results-over-Process"},
	"C04": {"name": "閉鎖的組織文化", "name_en": "Closed Culture"},
	"C05": {"name": "属人的経営", "name_en": "Personality-dependent Management"},
	"C06": {"name": "前例踏襲主義", "name_en": "Precedent-following"},
	"C07": {"name": "縦割り組織", "name_en": "Silo Mentality"},
	"C08": {"name": "不十分な倫理観", "name_en": "Insufficient Ethics"},
	"C09": {"name": "現場と経営の乖離", "name_en": "Management-field Gap"},
	"C10": {"name": "その他", "name_en": "Other Culture"},
}

ALL_LAYERS = {"A": LAYER_A, "B": LAYER_B, "C": LAYER_C}


def get_category(code):
	"""Get category info by code (e.g. 'A01')."""
	layer = code[0]
	layer_dict = ALL_LAYERS.get(layer, {})
	return layer_dict.get(code)


def get_layer(layer_key):
	"""Get all categories in a layer ('A', 'B', or 'C')."""
	return ALL_LAYERS.get(layer_key, {})


def get_all_categories():
	"""Get all categories across all layers."""
	result = []
	for layer_key, layer_dict in ALL_LAYERS.items():
		for code, info in layer_dict.items():
			result.append({
				"code": code,
				"layer": layer_key,
				"name": info["name"],
				"name_en": info["name_en"],
			})
	return result


def format_taxonomy_for_prompt():
	"""Format the full taxonomy as text for use in LLM prompts."""
	lines = []

	lines.append("## Layer A: 不正類型 (Incident Types)")
	for code, info in LAYER_A.items():
		lines.append(f"  {code}: {info['name']} ({info['name_en']})")

	lines.append("")
	lines.append("## Layer B: 組織メカニズム (Organizational Mechanisms)")
	for code, info in LAYER_B.items():
		lines.append(f"  {code}: {info['name']} ({info['name_en']})")

	lines.append("")
	lines.append("## Layer C: 組織文化 (Corporate Culture)")
	for code, info in LAYER_C.items():
		lines.append(f"  {code}: {info['name']} ({info['name_en']})")

	return "\n".join(lines)
