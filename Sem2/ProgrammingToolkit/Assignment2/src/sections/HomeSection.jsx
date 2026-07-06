import { useEffect, useState } from "react";
import GithubIcon from "../assets/github-svgrepo-com.svg";
import LinkedinIcon from "../assets/linkedin-svgrepo-com.svg";
import AvatarImage from "../assets/square.jpg";
import InfoCard from "../components/InfoCard";
import Card from "../components/Card";
import { getPersonalData } from "../services/profileApi";

function HomeSection() {
	const [personal, setPersonal] = useState(null);
	const [error, setError] = useState("");

	useEffect(() => {
		let isMounted = true;

		async function loadData() {
			try {
				const data = await getPersonalData();
				if (isMounted) {
					setPersonal(data);
					setError("");
				}
			} catch {
				if (isMounted) {
					setError("Could not load personal data.");
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

	if (!personal) {
		return (
			<section className="section">
				<p>Loading...</p>
			</section>
		);
	}

	const { social } = personal;

	return (
		<section className="section">

			<div className="hero">
				<div className="hero-avatar">
					<div className="avatar-ring" />
					<img
						className="avatar-image"
						src={AvatarImage}
						alt={`${personal.name} avatar`}
					/>
				</div>
				<div>
					<p className="hero-eyebrow">Hello, I'm</p>
					<h1 className="hero-name">{personal.name}</h1>
					<p className="hero-title">{personal.title}</p>
					<p className="hero-location">{personal.location}</p>
					<div className="nav-social">
						<a
							href={social.github}
							target="_blank"
							rel="noreferrer"
							aria-label="GitHub"
						>
							<img
								className="socials-icon"
								src={GithubIcon}
								alt="GitHub"
							/>
						</a>
						<a
							href={social.linkedin}
							target="_blank"
							rel="noreferrer"
							aria-label="LinkedIn"
						>
							<img
								className="socials-icon"
								src={LinkedinIcon}
								alt="LinkedIn"
							/>
						</a>
					</div>
				</div>
			</div>

			<div className="info-grid">
				{personal.dateOfBirth && (
					<InfoCard
						label="Date of Birth"
						value={personal.dateOfBirth}
						icon="🎂"
					/>
				)}
				{personal.email && (
					<InfoCard label="Email" value={personal.email} icon="✉️" />
				)}
				{personal.phone && (
					<InfoCard label="Phone" value={personal.phone} icon="📞" />
				)}
				{personal.languages?.length > 0 && (
					<InfoCard
						label="Languages"
						value={personal.languages.join(" - ")}
						icon="🌐"
					/>
				)}
			</div>

			<Card title="Places I've Lived">
				<div className="tags">
					{(personal.placesLived || []).map((p, i) => (
						<span key={i} className="tag">
							{p}
						</span>
					))}
				</div>
			</Card>
		</section>
	);
}

export default HomeSection;