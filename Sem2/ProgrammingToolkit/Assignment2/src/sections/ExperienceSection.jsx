import { useEffect, useState } from "react";
import SectionHeader from "../components/SectionHeader";
import Card from "../components/Card";
import FadeCard from "../components/FadeCard";
import { getProfessionalData } from "../services/profileApi";

function ExperienceSection() {
	const [professional, setProfessional] = useState(null);
	const [error, setError] = useState("");

	useEffect(() => {
		let isMounted = true;

		async function loadData() {
			try {
				const data = await getProfessionalData();
				if (isMounted) {
					setProfessional(data);
					setError("");
				}
			} catch {
				if (isMounted) {
					setError("Could not load professional data.");
				}
			}
		}

		loadData();

		return () => {
			isMounted = false;
		};
	}, []);

	if (error) {
		return (
			<section className="section">
				<p>{error}</p>
			</section>
		);
	}

	if (!professional) {
		return (
			<section className="section">
				<p>Loading...</p>
			</section>
		);
	}

	return (
		<section className="section">
			<SectionHeader title="Experience" />

			<Card title="Experience">
				{(professional.experience || []).map((exp, i) => (
					<FadeCard key={i}>
						<div>
							<h3 className="exp-role">{exp.role}</h3>
							<p className="exp-company">
								{exp.company} ·{" "}
								<span className="exp-period">
									{exp.period}
								</span>
							</p>
						</div>
					</FadeCard>
				))}
			</Card>

			<Card title="Skills">
				{(professional.skills || []).map((s, i) => (
					<div key={i} className="skill-group">
						<p className="skill-category">{s.category}</p>
						<div className="tags">
							{s.items.map((item, j) => (
								<span key={j} className="tag">
									{item}
								</span>
							))}
						</div>
					</div>
				))}
			</Card>

			<Card title="Certifications">
				{(professional.certifications || []).map((c, i) => (
					<FadeCard key={i}>
						<div>
							<h3 className="exp-role">{c.name}</h3>
							<p className="exp-company">
								{c.issuer} ·{" "}
								<span className="exp-period">{c.year}</span>
							</p>
						</div>
					</FadeCard>
				))}
			</Card>
		</section>
	);
}

export default ExperienceSection;
