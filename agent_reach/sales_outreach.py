# -*- coding: utf-8 -*-
"""
Sales & Outreach Templates — Agent Reach Geopolitical Tourism Radar.

Pre-built email templates for pitching the Diplomatic Impact Tracker
to key stakeholders following a Head-of-State economic mission.

Usage:
    from agent_reach.sales_outreach import (
        email_minister_template,
        email_hotel_chain_template,
        email_tato_template,
        sales_pitch_script,
    )

    # Print the email to send to Tanzania Ministry of Tourism
    print(email_minister_template(
        recipient_name="Permanent Secretary",
        sender_name="Your Name",
        sender_title="CEO, Your Company",
    ))
"""

from datetime import datetime


def email_minister_template(
    recipient_name: str = "Permanent Secretary",
    sender_name: str = "Your Name",
    sender_title: str = "CEO, Your SaaS Company",
    report_finding: str = "a measurable surge in Russian digital interest regarding Tanzanian tourism and investment opportunities",
) -> str:
    """Email template for Tanzania Ministry of Natural Resources and Tourism.

    This email is designed to prove the President's trip is working by
    showing real-time diplomatic impact data.
    """
    date_str = datetime.now().strftime("%B %d, %Y")
    return f"""Subject: 📊 Diplomatic Dividend: What Russia & China Are Saying About Tanzania This Week

Dear {recipient_name},

Following President Samia Suluhu Hassan's recent economic mission to Russia and deepening engagement with China, we have deployed our **Geopolitical Tourism Radar** — an AI-powered intelligence system that tracks diplomatic "tailwinds" in real-time.

Our system monitors XiaoHongShu, Weibo, Bilibili, Russian travel forums (awd.ru, Pikabu), VK, Yandex, and global news sources across **36 high-intent keywords** in Russian, Mandarin, and English related to Tanzanian tourism, investment, and logistics.

**Key Finding This Week:**
Our scans indicate {report_finding}. Local businesses and the tourism board are currently flying blind — they don't know what foreign delegations are asking about on platforms like XiaoHongShu or Russian forums.

**How We Can Help the Ministry:**
1. **Weekly "Diplomatic Dividend" Reports** — actionable PDF summaries of what foreign audiences are searching, asking, and posting about Tanzania
2. **Real-Time Alerts** — instant notifications when Russian or Chinese interest in visas, direct flights, or investment spikes
3. **Competitive Intelligence** — compare Tanzania's digital presence against Kenya, Rwanda, and other East African destinations

I would be delighted to schedule a 20-minute demonstration for your team this week to show you the live dashboard and discuss how the Ministry can align its marketing with this wave of foreign interest while the iron is hot.

Best regards,

{sender_name}
{sender_title}
{sender_name} | Agent Reach Geopolitical Tourism Radar
{sender_email()}
{sender_phone()}
"""


def email_hotel_chain_template(
    recipient_name: str = "General Manager",
    hotel_name: str = "Serengeti Serena Safari Lodge",
    sender_name: str = "Your Name",
    sender_title: str = "CEO, Your SaaS Company",
) -> str:
    """Email template for luxury hotel chains and resort groups (e.g., Serena Hotels, Zanzibar resorts).

    Focuses on capturing high-spending B2B and luxury travelers from Russia and China.
    """
    date_str = datetime.now().strftime("%B %d, %Y")
    return f"""Subject: 🚨 Russian & Chinese Travelers Are Looking for Tanzania — Is {hotel_name} Ready?

Dear {recipient_name},

President Samia's recent diplomatic missions to Russia and China have created a massive, measurable surge in foreign interest in Tanzanian tourism. But here's the problem:

**Most hotels are flying blind.**

While state media publishes articles about the new economic partnerships, Russian tourists are already asking on travel forums (awd.ru):
- "Are there direct flights from Moscow to Zanzibar yet?"
- "Can I use my Russian card in Tanzania now?"
- "Which luxury lodges in Serengeti accept foreign guests?"

Meanwhile, Chinese travelers on XiaoHongShu and Weibo are actively discussing Tanzania as their next destination — but they're confused about visa policies and luxury options.

**Our Geopolitical Tourism Radar** tracks this exact conversation in real-time across 13 platforms in 3 languages. We can tell you:
- What specific questions Russian travelers are asking about your hotel
- Which Chinese KOLs are planning Tanzania content
- When to update your booking pages in Russian/Mandarin
- Where to focus your ad spend to capture this diplomatic tailwind

**One-Page Special Report Attached**
I've prepared a complimentary 1-page PDF: *"The Diplomatic Dividend: What Russia & China Are Saying About Tanzania This Week"* — tailored specifically for the luxury hospitality sector.

I'll follow up next week, but if you'd like an early look at the dashboard, simply reply to this email.

Warm regards,

{sender_name}
{sender_title}
Agent Reach | Geopolitical Intelligence for Tourism
{sender_email()}
"""


def email_tato_template(
    recipient_name: str = "Executive Secretary",
    sender_name: str = "Your Name",
    sender_title: str = "CEO, Your SaaS Company",
    organization: str = "Tanzania Association of Tour Operators (TATO)",
) -> str:
    """Email template for Tanzania Association of Tour Operators (TATO).

    Positions the radar as a member benefit / industry intelligence tool.
    """
    date_str = datetime.now().strftime("%B %d, %Y")
    return f"""Subject: 🌍 New Intelligence Tool for TATO Members: Track the Diplomatic Tourism Wave

Dear {recipient_name},

The President's economic mission to Russia marks a historic opportunity for Tanzanian tourism. Russian and Chinese markets are showing unprecedented interest in Tanzania — but our local tour operators lack the intelligence to capitalize on it.

**The Problem:**
While state media celebrates the diplomatic success, Tanzanian tour operators are reading generic news articles. Meanwhile, Russian forums (awd.ru, Pikabu) and Chinese platforms (XiaoHongShu, Weibo, Bilibili) are buzzing with specific questions about:
- New direct charter flights from Moscow and Beijing
- Payment logistics (Russian cards, UnionPay acceptance)
- Visa-on-arrival procedures for Russian/Chinese passport holders
- Luxury safari and Zanzibar resort recommendations

**Our Solution:**
We've deployed a **Geopolitical Tourism Radar** specifically for this moment. It monitors 36 keywords across 13 platforms in Russian, Mandarin, and English — detecting exactly what foreign tourists are asking, searching, and sharing about Tanzania.

**Proposal for TATO:**
I'd like to offer TATO members a **complimentary pilot dashboard** for the next 30 days, including:
1. Weekly "Diplomatic Dividend" reports summarizing foreign digital sentiment
2. Real-time alerts for emerging topics (flight inquiries, visa questions, payment concerns)
3. A member-exclusive briefing on how to update websites and booking flows for Russian/Chinese guests

This is a zero-cost, high-impact tool that will give your members a first-mover advantage in capturing this diplomatic tailwind.

Would you be available for a 15-minute call this week to discuss onboarding TATO members?

Best regards,

{sender_name}
{sender_title}
Agent Reach | Geopolitical Tourism Intelligence
{sender_email()}
"""


def email_tic_template(
    recipient_name: str = "Executive Director",
    sender_name: str = "Your Name",
    sender_title: str = "CEO, Your SaaS Company",
) -> str:
    """Email template for Tanzania Investment Centre (TIC).

    Focuses on B2B investment interest from Russian and Chinese corporations.
    """
    date_str = datetime.now().strftime("%B %d, %Y")
    return f"""Subject: 📈 Tracking the Investment Tailwind: Russian & Chinese Investor Interest in Tanzania

Dear {recipient_name},

Following President Samia's economic missions, Tanzania Investment Centre is poised to receive increased inquiries from Russian and Chinese corporations. However, traditional economic reporting has a lag of 3-6 months.

Our **Geopolitical Tourism Radar** eliminates this lag by monitoring real-time digital signals from the exact platforms where corporate decision-makers and high-net-worth individuals discuss investment opportunities.

**What We're Already Detecting:**
- Russian-language discussions about Tanzania's mining and agriculture sectors on business forums
- Chinese WeChat Official Accounts posting about Tanzania Belt and Road opportunities
- Bilibili videos analyzing Tanzania's infrastructure projects
- Corporate delegation travel plans being discussed on professional networks

**How TIC Can Use This:**
1. **Proactive Outreach** — Identify the specific industries generating the most foreign interest this week
2. **Targeted Marketing** — Publish Mandarin/Russian investment brochures optimized for the topics being searched
3. **Event Intelligence** — Know when Russian/Chinese business delegations are planning to visit before they arrive
4. **Competitive Positioning** — Compare Tanzania's digital investment sentiment vs. Kenya, Zambia, and Ghana

I would be honored to demonstrate this capability to your investment promotion team. A 20-minute session will show you exactly how to turn diplomatic handshakes into measurable investment inquiries.

Looking forward to your response.

Cordially,

{sender_name}
{sender_title}
Agent Reach | Investment Intelligence Division
{sender_email()}
{sender_phone()}
"""


def sales_pitch_script(prospect_name: str = "[Prospect Name]", company: str = "[Company]") -> str:
    """Cold calling / in-person pitch script for the Diplomatic Dividend."""

    return f"""
=== COLD CALL / MEETING SCRIPT: The Diplomatic Dividend Pitch ===

OPENING (15 sec):
"Hi {prospect_name}, this is [Your Name]. I'm reaching out because
following President Samia's economic mission to Russia, we're seeing
a massive untracked surge in Russian and Chinese digital interest
regarding Tanzanian tourism and investment — but local businesses
are flying blind. I'd like to show you the data."

THE PROBLEM (30 sec):
"The President's trip made headlines, but the real signal is in
platforms like XiaoHongShu, Bilibili, Weibo, and Russian travel
forums like awd.ru. Russian tourists are asking about direct
flights, Chinese investors are researching mining opportunities,
but Tanzanian businesses don't know what questions are being asked."

THE SOLUTION (30 sec):
"We built a Geopolitical Tourism Radar that tracks 36 keywords
across 13 platforms in Russian, Mandarin, and English. It detects
exactly when foreign interest surges — whether it's about visas,
flights, payment logistics, or luxury accommodation — and sends
alerts so businesses can respond before their competitors."

THE OUTPUT (15 sec):
"We generate a 1-page 'Diplomatic Dividend' report each week.
For example, this week we detected [insert real finding, e.g.,
Russian forums asking about payment methods in Zanzibar].
Your team can use this to update website content, create targeted
ads, and prepare for incoming delegations."

CLOSE (15 sec):
"I'd like to offer you a complimentary look at the dashboard and
a personalized report for {company}. When do you have 20 minutes
this week?"

====================
"""


def sender_email() -> str:
    """Return the sender email address.

    Override this function or set AGENT_REACH_SALES_EMAIL env var.
    """
    import os
    return os.environ.get("AGENT_REACH_SALES_EMAIL", "your@email.com")


def sender_phone() -> str:
    """Return the sender phone number.

    Override this function or set AGENT_REACH_SALES_PHONE env var.
    """
    import os
    return os.environ.get("AGENT_REACH_SALES_PHONE", "+255 XXX XXX XXX")


def print_all_templates():
    """Print all available templates for quick reference."""
    templates = [
        ("Ministry of Natural Resources and Tourism", email_minister_template),
        ("Hotel Chain (e.g., Serena/Zanzibar Luxury)", email_hotel_chain_template),
        ("Tanzania Association of Tour Operators (TATO)", email_tato_template),
        ("Tanzania Investment Centre (TIC)", email_tic_template),
    ]

    print("=" * 70)
    print("  AGENT REACH — SALES OUTREACH TEMPLATES")
    print("=" * 70)
    print()
    print("Available templates:")
    print("-" * 50)
    for i, (name, func) in enumerate(templates, 1):
        print(f"  {i}. {name}")
    print()
    print("Usage Examples:")
    print("-" * 50)
    print("  from agent_reach.sales_outreach import email_minister_template")
    print('  email = email_minister_template(')
    print('      recipient_name="Permanent Secretary",')
    print('      sender_name="John Doe",')
    print('      sender_title="CEO, Tourism Intelligence Inc.",')
    print('  )')
    print('  print(email)')
    print()
    print("  from agent_reach.sales_outreach import sales_pitch_script")
    print('  print(sales_pitch_script("Mr. Mwangi", "Serengeti Serena"))')
    print()
    print("=" * 70)


if __name__ == "__main__":
    print_all_templates()