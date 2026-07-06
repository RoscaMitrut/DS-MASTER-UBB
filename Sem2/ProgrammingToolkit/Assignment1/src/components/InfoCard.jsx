function InfoCard({ label, value, icon }) {
	return (
		<div className="info-card">
			<span className="info-icon">{icon}</span>
			<p className="info-label">{label}</p>
			<p className="info-value">{value}</p>
		</div>
	);
}

export default InfoCard;