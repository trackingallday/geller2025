from django.core.management.base import BaseCommand
from chemsapp.models import NewsArticle
from django.utils.timezone import now, timedelta
import random

class Command(BaseCommand):
    help = 'Generates 10 demo news posts for Geller'

    def handle(self, *args, **options):
        news_data = [
            {
                "title": "Geller Launches Ultimo Odor Control Range",
                "content": "Geller introduces Ultimo, a revolutionary odor control system for healthcare and hospitality sectors. The enzymatic formula eliminates odors at the molecular level, surpassing traditional masking solutions.",
                "page": "news",
                "postType": "Product Launch",
                "isFeatured": True,
                "linkText": "Explore Ultimo",
                "linkURL": "/products/odour-control"
            },
            {
                "title": "MPI Approves Geller's CitruSuds Dishwash for Dairy Sector",
                "content": "After rigorous testing, MPI has expanded CitruSuds Dishwash's approval to include dairy processing facilities. The free-rinsing formula now helps NZ dairy exporters meet international hygiene standards.",
                "page": "news",
                "postType": "Certification",
                "isFeatured": False,
                "linkText": "View MPI Guidelines",
                "linkURL": "/support/mpi-guidelines"
            },
            {
                "title": "Geller Pro Floor System Reduces Hospital Slip Incidents by 42%",
                "content": "Auckland District Health Board reports significant safety improvements after adopting Geller Pro Floor's anti-microbial coating system, with fewer slip-related ACC claims across their facilities.",
                "page": "news",
                "postType": "Case Study",
                "isFeatured": True,
                "linkText": "Download Case Study",
                "linkURL": "/systems/pro-floor"
            },
            {
                "title": "New Online Training Platform: 360 Food Retail Certification",
                "content": "Geller's interactive training modules now cover end-to-end food retail hygiene, with MPI-compliant certification for staff. The platform features hazard simulation and NZQA-recognized assessments.",
                "page": "news",
                "postType": "Training",
                "isFeatured": False,
                "linkText": "Start Training",
                "linkURL": "https://ultimoprotect.getlearnworlds.com/"
            },
            {
                "title": "SoftShield Hand Care Wins Sustainability Award",
                "content": "Geller's pH-balanced SoftShield range receives the NZ Eco Label Trust award for reducing dermatitis cases in industrial workplaces while using 100% recycled packaging.",
                "page": "news",
                "postType": "Award",
                "isFeatured": True,
                "linkText": "Shop SoftShield",
                "linkURL": "/products/hand-body-care"
            },
            {
                "title": "Geller Green Now CarbonNeutral Certified",
                "content": "All Geller Green plant-based cleaners achieve CarbonNeutral product certification through native forest regeneration projects, aligning with NZ's 2050 emissions targets.",
                "page": "news",
                "postType": "Sustainability",
                "isFeatured": False,
                "linkText": "View Range",
                "linkURL": "/products/geller-green"
            },
            {
                "title": "Automated Dilution Systems Cut Chemical Waste by 60%",
                "content": "Early adopters of Geller's SmartDose connected dispensing systems report dramatic cost savings and reduced environmental impact through precise chemical measurement.",
                "page": "news",
                "postType": "Innovation",
                "isFeatured": False,
                "linkText": "Book Demo",
                "linkURL": "/solutions/smartdose"
            },
            {
                "title": "Geller Technical Expands Medical-Grade Disinfectants",
                "content": "New EN14476-compliant disinfectants combat emerging pathogens in aged care facilities, with rapid 30-second kill times for norovirus and antibiotic-resistant organisms.",
                "page": "news",
                "postType": "Product Expansion",
                "isFeatured": True,
                "linkText": "Technical Datasheets",
                "linkURL": "/products/medical"
            },
            {
                "title": "Partnership with Sustainable Coastlines for Ocean Safe Formulas",
                "content": "Geller reformulates 12 industrial cleaners to be marine-life safe, removing phosphates and microplastics. Every purchase now funds beach clean-up initiatives.",
                "page": "news",
                "postType": "Partnership",
                "isFeatured": False,
                "linkText": "Read Commitment",
                "linkURL": "/about-us"
            },
            {
                "title": "Winter Preparedness Guide: Combatting Mold in Commercial Buildings",
                "content": "Geller's technical team publishes evidence-based protocols for preventing mold outbreaks in damp conditions, featuring new moisture-activated sanitizing sprays.",
                "page": "news",
                "postType": "Guide",
                "isFeatured": False,
                "linkText": "Download Guide",
                "linkURL": "/support/training-modules"
            }
        ]

        for i, data in enumerate(news_data):
            NewsArticle.objects.create(
                name="news-post-{}".format(i),
                title=data["title"],
                content=data["content"],
                page=data["page"],
                postType=data["postType"],
                isFeatured=data["isFeatured"],
                isActive=True,
                linkText=data["linkText"],
                linkURL=data["linkURL"],
                linkColor="#702F8A",  # Geller's purple from style guide
                postDate=now() - timedelta(days=random.randint(1, 120))
            )

        self.stdout.write(self.style.SUCCESS('Successfully created 10 news posts'))