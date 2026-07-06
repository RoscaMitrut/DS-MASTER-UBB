function HobbyCard({ hobby }) {
	return (
		<div className="hobby-card">
			<span className="hobby-icon">{hobby.icon}</span>
			<h3 className="hobby-title">{hobby.title}</h3>
			<p className="hobby-desc">{hobby.description}</p>
		</div>
	);
}

export default HobbyCard;