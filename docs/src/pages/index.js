import React from "react";
import Link from "@docusaurus/Link";
import useBaseUrl from "@docusaurus/useBaseUrl";
import useDocusaurusContext from "@docusaurus/useDocusaurusContext";
import Layout from "@theme/Layout";
import { ICONS, Watermark } from "../components/HomeIcons";
import institutionsData from "@site/static/institutions/institutions.json";

const SECTIONS = [
  {
    id: "discover",
    num: "01",
    title: "What is dashAI?",
    tag: "START HERE",
    chips: ["OVERVIEW", "INSTALL", "USE CASES"],
    desc: "For new users: overview, key features, installation, and use cases.",
    to: "/discover/overview",
  },
  {
    id: "learn",
    num: "02",
    title: "Tutorials & Guides",
    tag: "GUIDES",
    chips: ["TUTORIALS", "MODULES", "ML FLOWS"],
    desc: "Step by step tutorials, module guides, and complete ML flows.",
    to: "/learn/tutorials/upload-dataset",
  },
  {
    id: "deep-dive",
    num: "03",
    title: "Architecture & Internals",
    tag: "ADVANCED",
    chips: ["ARCHITECTURE", "REGISTRY", "METRICS"],
    desc: "Platform architecture, component registry, metrics, and explainability.",
    to: "/deep-dive/architecture",
  },
  {
    id: "build",
    num: "04",
    title: "API & Development",
    tag: "DEVELOP",
    chips: ["REST API", "PLUGINS", "DEV SETUP"],
    desc: "REST API reference, plugin development, dev setup, and contributing.",
    to: "/build/dev-setup",
  },
];

const ArrowIcon = () => (
  <svg
    width="16"
    height="16"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    aria-hidden="true"
  >
    <path d="M5 12h14M13 6l6 6-6 6" />
  </svg>
);

export default function Home() {
  const { siteConfig, i18n } = useDocusaurusContext();
  const baseUrl = useBaseUrl("/");
  const ackText =
    institutionsData.acknowledgments.text[i18n.currentLocale] ||
    institutionsData.acknowledgments.text.en;
  const logos = [
    ...institutionsData.institutions,
    ...institutionsData.acknowledgments.logos,
  ]
    .filter((inst) => inst.logo)
    .map((inst) => ({
      name: inst.fullName || inst.name,
      url: inst.url,
      src: baseUrl + inst.logo,
      small: inst.small,
    }));

  return (
    <Layout title="Documentation" description={siteConfig.tagline}>
      <div className="dashai-home">
        {/* ── Hero ── */}
        <section className="dashai-hero">
          <Watermark className="dashai-wm dashai-wm--hero" />
          <div className="dashai-hero__inner">
            <span className="dashai-hero__pill">
              <span className="dashai-hero__led" />
              DOCUMENTATION
              <span className="dashai-hero__sep">|</span>
              <span className="dashai-hero__pill-accent">OPEN SOURCE</span>
              <span className="dashai-hero__sep">|</span>
              <span className="dashai-hero__pill-accent">MIT</span>
            </span>
            <h1 className="dashai-hero__title">
              Your complete guide to{" "}
              <span className="dashai-hero__accent">dashAI</span>.
            </h1>
            <p className="dashai-hero__sub">
              Learn to train, evaluate, and explain machine learning models, no
              code required. Browse tutorials, architecture deep dives, and the
              full component reference.
            </p>
            <div className="dashai-hero__cta">
              <Link
                to="/discover/overview"
                className="dashai-btn dashai-btn--blue"
              >
                Get Started <ArrowIcon />
              </Link>
              <Link to="/components/tasks" className="dashai-btn">
                Component Reference
              </Link>
            </div>
          </div>
        </section>

        {/* ── Section 01 - doc sections ── */}
        <section className="dashai-section">
          <div className="dashai-wrap">
            <div className="dashai-sec-head">
              <span className="dashai-sec-head__eyebrow">
                <span className="num">[ 01 ]</span> &nbsp; START EXPLORING
              </span>
              <h2 className="dashai-sec-head__title">
                Where do you want to start?
              </h2>
              <p className="dashai-sec-head__lead">
                Four paths through the docs, from your first dataset to the
                platform's internals and API.
              </p>
            </div>

            <div className="dashai-cards">
              {SECTIONS.map((sec) => (
                <Link
                  key={sec.id}
                  to={sec.to}
                  className={`dashai-landing-card dashai-landing-card--${sec.id}`}
                >
                  <div className="dashai-landing-card__header">
                    <div className="dashai-landing-card__icon">
                      {ICONS[sec.id]}
                    </div>
                    <span className="dashai-landing-card__badge dashai-landing-card__tag">
                      {sec.tag}
                    </span>
                  </div>
                  <div className="dashai-landing-card__title">{sec.title}</div>
                  <div className="dashai-landing-card__desc">{sec.desc}</div>
                  <div className="dashai-landing-card__footer">
                    <div className="dashai-landing-card__chips">
                      {sec.chips.map((chip) => (
                        <span
                          key={chip}
                          className="dashai-landing-card__badge dashai-landing-card__chip"
                        >
                          {chip}
                        </span>
                      ))}
                    </div>
                    <span className="dashai-landing-card__arrow">→</span>
                  </div>
                </Link>
              ))}
            </div>

            {/* New to dashAI? - inline strip below the cards */}
            <div className="dashai-startcta">
              <div className="dashai-startcta__icon">
                <svg
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  aria-hidden="true"
                >
                  <path d="M9 18h6M10 22h4M12 2a7 7 0 0 0-4 12.7c.6.5 1 1.3 1 2.1h6c0-.8.4-1.6 1-2.1A7 7 0 0 0 12 2z" />
                </svg>
              </div>
              <div className="dashai-startcta__body">
                <div className="dashai-startcta__heading">New to dashAI?</div>
                <div className="dashai-startcta__text">
                  Follow the Getting Started guide to set up the workbench and
                  train your first model, step by step.
                </div>
              </div>
              <Link to="/discover/workbench" className="dashai-cta__btn">
                Get Started
              </Link>
            </div>
          </div>
        </section>

        {/* ── Acknowledgments - dark branded footer band ── */}
        <section className="dashai-cta-band dashai-footer-band">
          <Watermark className="dashai-wm dashai-wm--cta" />
          <div className="dashai-wrap dashai-footer-band__inner">
            <div className="dashai-footer-band__head">
              <span className="dashai-footer-band__eyebrow">
                <span className="num">[ 02 ]</span> &nbsp; ACKNOWLEDGMENTS
              </span>
              <h2 className="dashai-footer-band__title">
                Built across institutions
              </h2>
              <p className="dashai-footer-band__lead">{ackText}</p>
            </div>
            <div className="dashai-ack__logos">
              {logos.map((logo) => (
                <a
                  key={logo.name}
                  href={logo.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="dashai-ack__logo-card"
                  aria-label={logo.name}
                >
                  <img
                    className={`dashai-ack__logo${
                      logo.small ? " dashai-ack__logo--small" : ""
                    }`}
                    src={logo.src}
                    alt={logo.name}
                  />
                </a>
              ))}
            </div>
          </div>
        </section>
      </div>
    </Layout>
  );
}
