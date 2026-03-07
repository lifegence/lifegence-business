frappe.pages["compliance-dashboard"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("RAG Search"),
		single_column: true,
	});

	page.main.html(frappe.render_template("compliance_dashboard"));

	new ComplianceDashboard(page);
};

class ComplianceDashboard {
	constructor(page) {
		this.page = page;
		this.wrapper = page.main;
		this.search_results = [];
		this.stats = {};
		this.search_type = "hybrid";
		this.taxonomy = {};

		this.setup_filters();
		this.load_stats();
		this.load_taxonomy();
		this.bind_events();
	}

	setup_filters() {
		this.search_input = this.wrapper.find(".compliance-search-input");
		this.year_filter = this.wrapper.find(".compliance-year-filter");
		this.company_filter = this.wrapper.find(".compliance-company-filter");
		this.classification_filter = this.wrapper.find(".compliance-classification-filter");
		this.search_btn = this.wrapper.find(".compliance-search-btn");
		this.search_type_btns = this.wrapper.find(".compliance-search-type");
		this.results_area = this.wrapper.find(".compliance-results");
		this.stats_area = this.wrapper.find(".compliance-stats");

		// Load years for filter
		frappe.call({
			method: "lifegence_compliance.api.reports.get_years",
			callback: (r) => {
				if (r.message) {
					this.year_filter.append(`<option value="">${__("All Years")}</option>`);
					r.message.forEach((y) => {
						this.year_filter.append(
							`<option value="${y}">${y}</option>`
						);
					});
				}
			},
		});
	}

	load_taxonomy() {
		frappe.call({
			method: "lifegence_compliance.api.classification.get_taxonomy",
			callback: (r) => {
				if (r.message) {
					this.taxonomy = r.message;
					this.populate_classification_filter(r.message);
				}
			},
		});
	}

	populate_classification_filter(taxonomy) {
		const layers = taxonomy.layers || {};
		const layer_labels = {
			A: __("Incident Types"),
			B: __("Org Mechanisms"),
			C: __("Corp Culture"),
		};

		["A", "B", "C"].forEach((layer_key) => {
			const categories = layers[layer_key] || [];
			if (categories.length) {
				this.classification_filter.append(
					`<optgroup label="Layer ${layer_key}: ${layer_labels[layer_key]}">`
				);
				categories.forEach((cat) => {
					this.classification_filter.append(
						`<option value="${cat.category_code}">${cat.category_code}: ${cat.category_name}</option>`
					);
				});
				this.classification_filter.append("</optgroup>");
			}
		});
	}

	bind_events() {
		this.search_btn.on("click", () => this.do_search());
		this.search_input.on("keypress", (e) => {
			if (e.which === 13) this.do_search();
		});

		// Search type toggle
		this.search_type_btns.on("click", "button", (e) => {
			this.search_type_btns.find("button").removeClass("active");
			$(e.currentTarget).addClass("active");
			this.search_type = $(e.currentTarget).data("type");
		});

		// Click result to navigate to report
		this.wrapper.on("click", ".result-item", (e) => {
			const report_name = $(e.currentTarget).data("report");
			if (report_name) {
				frappe.set_route("Form", "Committee Report", report_name);
			}
		});
	}

	load_stats() {
		frappe.call({
			method: "lifegence_compliance.api.reports.get_stats",
			callback: (r) => {
				if (r.message) {
					this.stats = r.message;
					this.render_stats();
				}
			},
		});
	}

	render_stats() {
		const s = this.stats;
		this.stats_area.html(`
			<div class="row">
				<div class="col-md-2">
					<div class="stat-card">
						<div class="stat-value">${s.total_reports || 0}</div>
						<div class="stat-label">${__("Total Reports")}</div>
					</div>
				</div>
				<div class="col-md-2">
					<div class="stat-card">
						<div class="stat-value">${s.indexed_reports || 0}</div>
						<div class="stat-label">${__("Indexed")}</div>
					</div>
				</div>
				<div class="col-md-2">
					<div class="stat-card">
						<div class="stat-value">${s.classified_reports || 0}</div>
						<div class="stat-label">${__("Classified")}</div>
					</div>
				</div>
				<div class="col-md-2">
					<div class="stat-card">
						<div class="stat-value">${s.total_chunks || 0}</div>
						<div class="stat-label">${__("Chunks")}</div>
					</div>
				</div>
				<div class="col-md-2">
					<div class="stat-card">
						<div class="stat-value">${s.unique_companies || 0}</div>
						<div class="stat-label">${__("Companies")}</div>
					</div>
				</div>
				<div class="col-md-2">
					<div class="stat-card">
						<div class="stat-value">${s.earliest_year || "-"} - ${s.latest_year || "-"}</div>
						<div class="stat-label">${__("Year Range")}</div>
					</div>
				</div>
			</div>
		`);
	}

	get_search_method() {
		const methods = {
			hybrid: "lifegence_compliance.api.search.hybrid_search",
			vector: "lifegence_compliance.api.search.vector_search",
			fulltext: "lifegence_compliance.api.search.fulltext_search",
		};
		return methods[this.search_type] || methods.hybrid;
	}

	do_search() {
		const query = this.search_input.val().trim();
		if (!query) {
			frappe.show_alert(__("Please enter a search query"));
			return;
		}

		const year = this.year_filter.val();
		const company_name = this.company_filter.val().trim();
		const classification = this.classification_filter.val();

		this.results_area.html(
			'<div class="text-center p-5"><div class="spinner-border"></div></div>'
		);

		const args = {
			query,
			limit: 20,
			group_by_report: "1",
		};
		if (year) args.year = year;
		if (company_name) args.company_name = company_name;
		if (classification) args.classification = classification;

		const method = this.get_search_method();

		frappe.call({
			method: method,
			args: args,
			callback: (r) => {
				if (r.message) {
					this.search_results = r.message.results || [];
					this.render_results(r.message);
				}
			},
			error: () => {
				this.results_area.html(
					`<div class="text-center text-muted p-5">${__("Search failed. Please try again.")}</div>`
				);
			},
		});
	}

	get_badge_class(code) {
		if (!code) return "badge-secondary";
		const layer = code.charAt(0);
		if (layer === "A") return "badge-danger";
		if (layer === "B") return "badge-primary";
		if (layer === "C") return "badge-success";
		return "badge-secondary";
	}

	get_category_name(code) {
		if (!this.taxonomy || !this.taxonomy.categories) return code;
		const cat = this.taxonomy.categories.find((c) => c.category_code === code);
		return cat ? cat.category_name : code;
	}

	render_results(data) {
		if (!data.results || data.results.length === 0) {
			this.results_area.html(
				`<div class="text-center text-muted p-5">${__("No results found")}</div>`
			);
			return;
		}

		const search_type_label = {
			hybrid: __("Hybrid"),
			vector: __("Vector"),
			fulltext: __("Full-text"),
		};

		let html = `<div class="search-meta mb-3">
			<small class="text-muted">
				${data.count} ${__("results")} for "${frappe.utils.escape_html(data.query)}"
				(${search_type_label[data.search_type] || data.search_type})
				${data.grouped ? " - " + __("grouped by report") : ""}
			</small>
		</div>`;

		data.results.forEach((r) => {
			const score = r.best_score
				? r.best_score.toFixed(3)
				: r.hybrid_score
					? r.hybrid_score.toFixed(3)
					: r.score
						? r.score.toFixed(3)
						: "-";

			const score_pct = Math.min(
				100,
				Math.round(
					(r.best_score || r.hybrid_score || r.score || 0) * 100
				)
			);

			const content_preview =
				r.content && r.content.length > 200
					? r.content.substring(0, 200) + "..."
					: r.content || "";

			const classifications = (r.classifications || [])
				.map(
					(c) =>
						`<span class="badge ${this.get_badge_class(c)}" title="${this.get_category_name(c)}">${c}</span>`
				)
				.join(" ");

			const matched_chunks_label = r.matched_chunks
				? `<span class="badge badge-light">${r.matched_chunks} ${__("chunks matched")}</span>`
				: "";

			html += `
				<div class="result-item card mb-2 p-3" data-report="${frappe.utils.escape_html(r.report_name)}" style="cursor:pointer">
					<div class="d-flex justify-content-between align-items-start">
						<div>
							<strong class="result-company">${frappe.utils.escape_html(r.company_name || "")}</strong>
							<span class="text-muted ml-2">(${r.year || ""})</span>
							${matched_chunks_label}
						</div>
						<div class="text-right">
							<div class="score-bar-wrapper">
								<div class="score-bar" style="width: ${score_pct}%"></div>
							</div>
							<small class="text-muted">${__("Score")}: ${score}</small>
						</div>
					</div>
					<div class="mt-1">
						<small class="text-muted result-report-name">${frappe.utils.escape_html(r.report_name || "")}</small>
					</div>
					<div class="mt-2 text-muted small result-content-preview">${frappe.utils.escape_html(content_preview)}</div>
					${classifications ? `<div class="mt-2 result-classifications">${classifications}</div>` : ""}
				</div>
			`;
		});

		this.results_area.html(html);
	}
}
