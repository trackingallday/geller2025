import os
import random
from django.core.management.base import BaseCommand
from django.conf import settings
from chemsapp.models import MarketSector, MarketSectorSection  # Replace 'your_app' with your app name

class Command(BaseCommand):
    help = 'Creates 4 sector sections for each sector with random images'

    def handle(self, *args, **options):
        # Get all available sectors
        sectors = MarketSector.objects.all()
        
        if not sectors.exists():
            self.stdout.write(self.style.ERROR('No sectors found. Please create sectors first.'))
            return

        # Get all images from the commands/images folder
        images_dir = os.path.join(os.path.dirname(__file__), 'images')
        try:
            image_files = [f for f in os.listdir(images_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
        except OSError:
            self.stdout.write(self.style.ERROR('Images directory not found. Please create a "images" folder in commands/'))
            return

        if not image_files:
            self.stdout.write(self.style.ERROR('No images found in the images directory'))
            return

        # Section templates for different sectors
        section_templates = {
            'Healthcare & Medical': [
                {"title": "Infection Control Solutions", "description": "Specialized disinfectants for hospital-grade sanitation that meet EN standards for healthcare environments."},
                {"title": "Aged Care Protocols", "description": "Gentle yet effective cleaning systems designed specifically for sensitive aged care facility needs."},
                {"title": "Medical Equipment Care", "description": "Non-corrosive cleaners that safely sanitize sensitive medical instruments and surfaces."},
                {"title": "Outbreak Response", "description": "Rapid-deployment cleaning kits for managing infectious disease outbreaks in clinical settings."}
            ],
            'Hospitality & Kitchen': [
                {"title": "Warewash Optimization", "description": "Complete dish and glass washing systems that deliver the lowest cost per wash in NZ."},
                {"title": "Grease Management", "description": "High-performance degreasers that keep commercial kitchens running safely and efficiently."},
                {"title": "Food Contact Sanitizers", "description": "MPI-approved sanitizers for all food preparation surfaces and equipment."},
                {"title": "Bar & Beverage Care", "description": "Specialty cleaners that maintain glassware clarity and remove stubborn beverage residues."}
            ],
            # Add templates for all 8 sectors
            'Industrial & Transport': [
                {"title": "Heavy-Duty Degreasers", "description": "Industrial-strength formulas that cut through tough grease and oil in workshop environments."},
                {"title": "Fleet Cleaning Systems", "description": "Vehicle wash solutions that protect paintwork while removing road grime and salt."},
                {"title": "Machine Maintenance", "description": "Non-foaming cleaners that safely maintain industrial equipment."},
                {"title": "Workshop Safety", "description": "Spill control and surface treatments that reduce slip hazards in industrial spaces."}
            ],
            'Janitorial & Commercial Cleaning': [
                {"title": "Floor Care Systems", "description": "Complete solutions for all floor types from hardwood to vinyl composition tile."},
                {"title": "Restroom Sanitation", "description": "Hygienic cleaning and odor control systems for high-traffic restrooms."},
                {"title": "Green Cleaning", "description": "Eco-certified products that deliver results without harsh chemicals."},
                {"title": "Day Cleaning", "description": "Low-odor daytime cleaning solutions for occupied spaces."}
            ],
            'Retail & Food Services': [
                {"title": "Food Retail Hygiene", "description": "360 cleaning systems for supermarkets and grocery environments."},
                {"title": "Display Case Care", "description": "Streak-free cleaners for glass and stainless steel food displays."},
                {"title": "Food Court Maintenance", "description": "High-traffic area solutions that maintain cleanliness between service periods."},
                {"title": "Retail Entrance Systems", "description": "Matting and cleaning protocols that reduce dirt ingress in retail spaces."}
            ],
            'Aged Care & Facilities': [
                {"title": "Dementia Care Cleaning", "description": "Specialized protocols for memory care unit hygiene and safety."},
                {"title": "Resident Room Care", "description": "Gentle daily cleaning systems that respect resident privacy and comfort."},
                {"title": "Common Area Hygiene", "description": "High-frequency touchpoint cleaning for lounges and activity areas."},
                {"title": "Linen Management", "description": "Infection-controlled laundry systems for aged care facilities."}
            ],
            'Laundry & Textile Care': [
                {"title": "Commercial Laundry Systems", "description": "Complete chemical and equipment solutions for high-volume laundries."},
                {"title": "Linen Life Extension", "description": "Programs that reduce replacement costs by extending textile lifespan."},
                {"title": "Healthcare Laundry", "description": "Infection-controlled washing systems for healthcare linens."},
                {"title": "Eco Laundry", "description": "Sustainable laundry solutions that reduce water and energy use."}
            ],
            'Education & Public Sector': [
                {"title": "School Hygiene", "description": "Child-safe cleaning systems for classrooms and play areas."},
                {"title": "Sports Facility Care", "description": "Specialized cleaners for gyms, pools, and locker rooms."},
                {"title": "Government Buildings", "description": "Security-conscious cleaning protocols for sensitive government facilities."},
                {"title": "Campus-Wide Systems", "description": "Unified cleaning programs for universities and large institutions."}
            ]
        }

        created_count = 0
        for sector in sectors:
            # Get the template for this sector or use a default
            templates = section_templates.get(sector.name, [
                {
                    "title": "{} Solution 1".format(sector.name),
                    "description": "Specialized cleaning solution for {} applications.".format(sector.name)
                },
                {
                    "title": "{} Solution 2".format(sector.name),
                    "description": "Advanced hygiene protocol for {} environments.".format(sector.name)
                },
                {
                    "title": "{} System 1".format(sector.name),
                    "description": "Complete system approach to {} cleaning challenges.".format(sector.name)
                },
                {
                    "title": "{} Innovation".format(sector.name),
                    "description": "Cutting-edge technology for {} facility management.".format(sector.name)
                }
            ])

            for template in templates:
                random_image = random.choice(image_files)
                image_path = os.path.join(images_dir, random_image)
                
                MarketSectorSection.objects.create(
                    title=template["title"],
                    description=template["description"],
                    sector=sector,
                    image=image_path  # Django will handle the FileField upload
                )
                created_count += 1

        self.stdout.write(self.style.SUCCESS('Successfully created sector sections'))