import { Activity, CircleAlert, Mail, UserRound } from 'lucide-react';

export default function Profile() {
  return (
    <div className="page-shell inner-page profile-page">
      <div className="page-breadcrumb"><span>WORKSPACE</span><i>/</i><strong>PROFILE</strong></div>
      <section className="inner-page-heading">
        <div>
          <div className="eyebrow"><span className="eyebrow-line" /> DEMO ACCOUNT</div>
          <h1>Your profile<span>.</span></h1>
          <p>Sample identity details for this browser-only demo session.</p>
        </div>
        <span className="outline-chip"><Activity size={13} /> DEMO ACCESS</span>
      </section>

      <section className="panel profile-card" aria-labelledby="profile-card-title">
        <div className="profile-card-heading">
          <span className="profile-avatar-large" aria-hidden="true">DU</span>
          <div>
            <div className="panel-kicker"><span className="panel-kicker-line" /> SAMPLE PROFILE</div>
            <h2 id="profile-card-title">Demo User</h2>
            <span className="profile-account-type">DEMO SESSION · NOT A REAL ACCOUNT</span>
          </div>
        </div>
        <div className="profile-details">
          <div><UserRound size={17} aria-hidden="true" /><span><small>DISPLAY NAME</small><strong>Demo User</strong></span></div>
          <div><Mail size={17} aria-hidden="true" /><span><small>EMAIL</small><strong>demo@gitlexa.local</strong></span></div>
        </div>
        <p className="profile-demo-notice"><CircleAlert size={16} aria-hidden="true" /> These details are illustrative demo data. Profile editing and account persistence are not available.</p>
      </section>
    </div>
  );
}
