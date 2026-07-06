import GithubIcon from "../assets/github-svgrepo-com.svg";
import LinkedinIcon from "../assets/linkedin-svgrepo-com.svg";
import AvatarImage from "../assets/square.jpg";
import profileData from "../constants/profileData";
import InfoCard from "../components/InfoCard";
import Card from "../components/Card";

function HomeSection() {
	const { personal } = profileData;
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
				{personal.languages && (
					<InfoCard
						label="Languages"
						value={personal.languages.join(" - ")}
						icon="🌐"
					/>
				)}
			</div>

			<Card title="Places I've Lived">
				<div className="tags">
					{personal.placesLived.map((p, i) => (
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