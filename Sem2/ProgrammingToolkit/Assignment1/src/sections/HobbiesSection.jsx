import profileData from "../constants/profileData";
import SectionHeader from "../components/SectionHeader";
import HobbyCard from "../components/HobbyCard";

function HobbiesSection() {
	const { hobbies } = profileData;
	return (
		<section className="section">
			<SectionHeader title="Hobbies & Passions" />
			<div className="hobbies-grid">
				{hobbies.passions.map((h, i) => (
					<HobbyCard key={i} hobby={h} />
				))}
			</div>
		</section>
	);
}

export default HobbiesSection;