import os
import csv
import uuid
import math
import random
from datetime import datetime, timedelta, time, timezone as dt_timezone
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from store.models import Receipt, ReceiptItem, Product

class Command(BaseCommand):
    help = 'Simulates realistic sales data and exports to CSV.'

    def add_arguments(self, parser):
        parser.add_argument('--start', type=str, default='2025-01-01', help='Start date (YYYY-MM-DD)')
        parser.add_argument('--end', type=str, default='2026-02-25', help='End date (YYYY-MM-DD)')
        parser.add_argument('--seed', type=int, default=42, help='Random seed')
        parser.add_argument('--outdir', type=str, default='data', help='Output directory for CSV files within BASE_DIR')
        parser.add_argument('--reset-simulated', action='store_true', help='Delete ONLY SIMULATED receipts in the date range before inserting')

    def handle(self, *args, **options):
        start_date_str = options['start']
        end_date_str = options['end']
        seed = options['seed']
        outdir_name = options['outdir']
        reset_sim_flag = options['reset_simulated']
        
        random.seed(seed)
        
        # Use simple UTC timezone to avoid timezone tracking issues with dummy data
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").replace(tzinfo=dt_timezone.utc)
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").replace(tzinfo=dt_timezone.utc)
        
        if reset_sim_flag:
            self.stdout.write(f"Deleting existing SIMULATED receipts from {start_date_str} to {end_date_str}...")
            deleted, _ = Receipt.objects.filter(
                source='SIMULATED',
                created_at__range=(start_date, end_date + timedelta(days=1))
            ).delete()
            self.stdout.write(f"Deleted {deleted} SIMULATED receipts.")
            
        products = list(Product.objects.select_related('category').filter(active=True))
        if not products:
            self.stdout.write(self.style.ERROR("No active products found in DB. Please run seed script first."))
            return
            
        # Product weights calculation
        product_weights = []
        for p in products:
            cat_name = p.category.name.lower()
            if 'signature' in cat_name:
                w = 2.0
            elif 'sparking' in cat_name or 'smoothie' in cat_name:
                w = 1.5
            elif 'matcha' in cat_name:
                w = 1.2
            elif 'weird' in cat_name:
                w = 0.5
            else:
                w = 1.0
            product_weights.append(w)
            
        total_days = (end_date - start_date).days
        if total_days < 0:
            self.stdout.write(self.style.ERROR("Start date must be before end date."))
            return
            
        # Intraday weights (07:00 - 18:00)
        intraday_weights_dict = {
            7: 0.5, 8: 1.0, 9: 0.8, 10: 0.7, 11: 0.6,
            12: 1.2, 13: 0.9, 14: 0.8, 15: 1.0, 16: 0.8, 17: 0.6
        }
        total_intraday_weight = sum(intraday_weights_dict.values())
        intraday_probs = {h: w / total_intraday_weight for h, w in intraday_weights_dict.items()}
        hours = list(intraday_probs.keys())
        probs = list(intraday_probs.values())
        
        seasonal_multipliers = {
            1: 1.0, 2: 1.0, 3: 1.1, 4: 1.2, 5: 1.15, 6: 0.9,
            7: 0.85, 8: 0.85, 9: 0.8, 10: 0.9, 11: 1.0, 12: 1.05
        }
        weekday_multipliers = [1.1, 0.9, 0.9, 1.0, 1.15, 1.0, 0.9] # Mon=0 ... Sun=6
        
        def iter_days(start, end):
            curr = start
            while curr <= end:
                yield curr
                curr += timedelta(days=1)
                
        receipts_to_create = []
        
        daily_stats = []
        hourly_stats = []
        transactions_csv = []
        receipts_csv = []
        
        self.stdout.write("Simulating sales data...")
        
        for day_index, current_date in enumerate(iter_days(start_date, end_date)):
            # Growth trend: logistic curve from ~65 to ~170
            L = 170.0 - 65.0
            k = 0.05
            x0 = total_days / 2.0
            trend_base = 65.0 + L / (1.0 + math.exp(-k * (day_index - x0)))
            
            # Apply multipliers
            wk_mult = weekday_multipliers[current_date.weekday()]
            seas_mult = seasonal_multipliers[current_date.month]
            
            expected_orders = trend_base * wk_mult * seas_mult
            
            # Add random noise (+/- 15%)
            noise = random.uniform(0.85, 1.15)
            daily_orders = int(round(expected_orders * noise))
            
            day_total_amount = Decimal('0.00')
            
            hour_assignments = random.choices(hours, weights=probs, k=daily_orders)
            
            hour_counts = {h: 0 for h in hours}
            for h in hour_assignments:
                hour_counts[h] += 1
                
            for h in hours:
                orders_this_hour = hour_counts[h]
                hr_total_amount = Decimal('0.00')
                
                for _ in range(orders_this_hour):
                    minute = random.randint(0, 59)
                    second = random.randint(0, 59)
                    order_time = current_date.replace(hour=h, minute=minute, second=second)
                    
                    receipt_id = f"REC-{order_time.strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"
                    
                    num_items = random.choices([1, 2, 3], weights=[0.65, 0.28, 0.07], k=1)[0]
                    selected_products = random.choices(products, weights=product_weights, k=num_items)
                    
                    order_total_items = 0
                    order_total_amount = Decimal('0.00')
                    
                    receipt_obj = Receipt(
                        receipt_id=receipt_id,
                        created_at=order_time,
                        total_items=0,
                        total_amount=Decimal('0.00'),
                        source='SIMULATED'
                    )
                    
                    order_items_objs = []
                    
                    for prod in selected_products:
                        qty = random.choices([1, 2], weights=[0.9, 0.1], k=1)[0]
                        unit_price = Decimal(prod.price) / Decimal('100.00')
                        line_total = unit_price * qty
                        
                        order_total_items += qty
                        order_total_amount += line_total
                        
                        item_obj = ReceiptItem(
                            receipt=receipt_obj, # Assign temporarily
                            product=prod,
                            product_name_snapshot=prod.name,
                            category_snapshot=prod.category.name,
                            qty=qty,
                            unit_price=unit_price,
                            line_total=line_total
                        )
                        order_items_objs.append(item_obj)
                        
                        transactions_csv.append({
                            'transaction_id': receipt_id,
                            'date': current_date.strftime('%Y-%m-%d'),
                            'hour': f"{h:02d}:00",
                            'product_name': prod.name,
                            'category': prod.category.name,
                            'qty': qty,
                            'unit_price': unit_price,
                            'line_total': line_total
                        })
                        
                    receipt_obj.total_items = order_total_items
                    receipt_obj.total_amount = order_total_amount
                    
                    receipts_to_create.append((receipt_obj, order_items_objs))
                    
                    receipts_csv.append({
                        'receipt_id': receipt_id,
                        'date': current_date.strftime('%Y-%m-%d'),
                        'hour': f"{h:02d}:00",
                        'total_items': order_total_items,
                        'total_amount': order_total_amount,
                        'source': 'SIMULATED'
                    })
                    
                    hr_total_amount += order_total_amount
                    
                hourly_stats.append({
                    'date': current_date.strftime('%Y-%m-%d'),
                    'hour': f"{h:02d}:00",
                    'total_receipts': orders_this_hour,
                    'total_amount': hr_total_amount
                })
                day_total_amount += hr_total_amount
                
            daily_stats.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'total_receipts': daily_orders,
                'total_amount': day_total_amount
            })

            # Progress output
            if day_index % 30 == 0:
                self.stdout.write(f"Processed up to {current_date.strftime('%Y-%m-%d')}...")

        self.stdout.write("Bulk inserting data into database...")
        
        BATCH_SIZE = 500
        
        all_receipts = [r[0] for r in receipts_to_create]
        Receipt.objects.bulk_create(all_receipts, batch_size=BATCH_SIZE, ignore_conflicts=True)
        
        # Now fetch the created receipts to get exact PKs
        all_receipt_ids = [r.receipt_id for r in all_receipts]
        
        db_receipts = {}
        for i in range(0, len(all_receipt_ids), BATCH_SIZE):
            chunk = all_receipt_ids[i:i+BATCH_SIZE]
            qs = Receipt.objects.filter(receipt_id__in=chunk).values_list('receipt_id', 'id')
            db_receipts.update(dict(qs))
            
        final_items_to_insert = []
        for r_obj, items in receipts_to_create:
            r_pk = db_receipts.get(r_obj.receipt_id)
            if r_pk:
                for item in items:
                    item.receipt_id = r_pk  # Use the hidden integer identifier to avoid lookup overhead
                    final_items_to_insert.append(item)
                    
        ReceiptItem.objects.bulk_create(final_items_to_insert, batch_size=BATCH_SIZE)
        
        self.stdout.write(self.style.SUCCESS(f"Inserted {len(all_receipts)} receipts and {len(final_items_to_insert)} items."))
        
        # Export CSVs
        out_path = os.path.join(settings.BASE_DIR, outdir_name)
        os.makedirs(out_path, exist_ok=True)
        
        self.stdout.write(f"Exporting CSVs to {out_path}...")
        
        with open(os.path.join(out_path, 'transactions.csv'), 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['transaction_id', 'date', 'hour', 'product_name', 'category', 'qty', 'unit_price', 'line_total'])
            writer.writeheader()
            writer.writerows(transactions_csv)
            
        with open(os.path.join(out_path, 'receipts.csv'), 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['receipt_id', 'date', 'hour', 'total_items', 'total_amount', 'source'])
            writer.writeheader()
            writer.writerows(receipts_csv)
            
        with open(os.path.join(out_path, 'hourly_sales.csv'), 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['date', 'hour', 'total_receipts', 'total_amount'])
            writer.writeheader()
            writer.writerows(hourly_stats)
            
        with open(os.path.join(out_path, 'daily_sales.csv'), 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['date', 'total_receipts', 'total_amount'])
            writer.writeheader()
            writer.writerows(daily_stats)
            
        self.stdout.write(self.style.SUCCESS('Data simulation and export completed successfully!'))
