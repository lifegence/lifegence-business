# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe


def calculate_risk_score(revenue=0, profit=0, capital=0, years_in_business=0,
						payment_history_score=0, existing_transaction_months=0,
						average_monthly_transaction=0):
	"""Calculate risk score from 5 weighted factors (0-100).

	Returns dict with score, grade, and recommended_limit.
	"""
	score = 0

	# Financial health (30 points)
	if revenue and revenue > 0 and profit is not None:
		margin = (profit / revenue) * 100
		if margin >= 5:
			score += 30
		elif margin >= 3:
			score += 20
		elif margin >= 0:
			score += 10

	# Business history (15 points)
	if years_in_business >= 10:
		score += 15
	elif years_in_business >= 5:
		score += 10
	elif years_in_business >= 3:
		score += 5

	# Capital (15 points)
	if capital >= 100_000_000:
		score += 15
	elif capital >= 10_000_000:
		score += 10
	elif capital >= 3_000_000:
		score += 5

	# Payment history (25 points)
	if payment_history_score:
		score += round(payment_history_score * 0.25)

	# Transaction history (15 points)
	if existing_transaction_months >= 24:
		score += 15
	elif existing_transaction_months >= 12:
		score += 10
	elif existing_transaction_months >= 6:
		score += 5

	score = min(score, 100)
	grade = determine_grade(score)
	recommended = calculate_recommended_limit(grade, average_monthly_transaction)

	return {
		"score": score,
		"grade": grade,
		"recommended_limit": recommended,
	}


def determine_grade(score):
	"""Determine risk grade (A-E) based on score."""
	settings = frappe.get_single("Credit Settings")
	if score >= (settings.grade_a_min_score or 80):
		return "A"
	elif score >= (settings.grade_b_min_score or 60):
		return "B"
	elif score >= (settings.grade_c_min_score or 40):
		return "C"
	elif score >= (settings.grade_d_min_score or 20):
		return "D"
	return "E"


def calculate_recommended_limit(grade, average_monthly_transaction=0):
	"""Calculate recommended credit limit based on grade and monthly transaction."""
	multipliers = {"A": 6, "B": 4, "C": 2, "D": 1, "E": 0}
	return (average_monthly_transaction or 0) * multipliers.get(grade, 0)
