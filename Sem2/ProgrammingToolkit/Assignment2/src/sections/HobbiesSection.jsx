import { useEffect, useState } from "react";
import SectionHeader from "../components/SectionHeader";
import HobbyCard from "../components/HobbyCard";
import { getHobbiesData } from "../services/profileApi";

function HobbiesSection() {
	const [hobbies, setHobbies] = useState(null);
	const [error, setError] = useState("");

	useEffect(() => {
		let isMounted = true;

		async function loadData() {
			try {
				const data = await getHobbiesData();
				if (isMounted) {
					setHobbies(data);
					setError("");
				}
			} catch {
				if (isMounted) {
					setError("Could not load hobbies data.");
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

	if (!hobbies) {
		return (
			<section className="section">
				<p>Loading...</p>
			</section>
		);
	}

	return (
		<section className="section">
			<SectionHeader title="Hobbies & Passions" />
			<div className="hobbies-grid">
				{(hobbies.passions || []).map((h, i) => (
					<HobbyCard key={i} hobby={h} />
				))}
			</div>
		</section>
	);
}

export default HobbiesSection;