#!/usr/bin/env python3
"""
Test script for the enhanced OCR functionality
This script helps test the OCR system with sample receipt data from different Nigerian banks
"""

import sys
import os

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Tracklytic_Backend.settings')

import django
django.setup()

from Tracker.utils import extract_transaction_data, detect_bank, detect_transaction_type_enhanced

def test_ocr_with_sample_data():
    """
    Test the OCR functionality with sample receipt text data
    """
    
    # Sample receipt data from different banks
    sample_receipts = {
        'GTBank': """
        GTBank
        Transaction Receipt
        Date: 15/12/2024
        Time: 14:30:25
        
        From: John Doe 1234567890
        To: Jane Smith 0987654321
        Amount: ₦50,000.00
        
        Transaction Type: Transfer Out
        Status: Successful
        
        Thank you for banking with GTBank
        """,
        
        'Access Bank': """
        ACCESS BANK
        Transaction Alert
        
        Date: 20-12-2024
        Account: 1122334455
        
        Sender: Mary Johnson
        Recipient: Peter Wilson
        Amount: NGN 25,000.00
        
        Type: Credit
        Reference: ACC123456
        """,
        
        'OPay': """
        OPay
        Transaction Receipt
        
        Date: 25/12/2024
        From: Alice Brown 08012345678
        To: Bob Davis 08087654321
        
        Amount: ₦15,000.00
        Transaction: Sent
        Status: Successful
        
        Thank you for using OPay
        """,
        
        'PalmPay': """
        PalmPay
        Transaction Details
        
        Date: 30-12-2024
        Sender: Carol White 08123456789
        Recipient: David Black 08987654321
        
        Amount: ₦75,000.00
        Type: Transfer
        Status: Completed
        """,
        
        'Zenith Bank': """
        ZENITH BANK
        Transaction Receipt
        
        Date: 05/01/2025
        Account: 9876543210
        
        From: Emma Wilson
        To: Frank Miller
        Amount: ₦100,000.00
        
        Transaction Type: Debit
        Reference: ZEN789012
        """,
        
        'First Bank': """
        FIRST BANK OF NIGERIA
        Transaction Alert
        
        Date: 10-01-2025
        Account: 1122334455
        
        Sender: Grace Lee
        Recipient: Henry Taylor
        Amount: NGN 45,000.00
        
        Type: Transfer Out
        Status: Successful
        """,
        
        'UBA': """
        UBA
        Transaction Receipt
        
        Date: 15/01/2025
        From: Irene Garcia 1234567890
        To: Jack Martinez 0987654321
        
        Amount: ₦30,000.00
        Transaction: Credit
        Reference: UBA456789
        """,
        
        'Ecobank': """
        ECOBANK
        Transaction Details
        
        Date: 20/01/2025
        Account: 9876543210
        
        Sender: Kelly Anderson
        Recipient: Lisa Thompson
        Amount: ₦60,000.00
        
        Type: Debit
        Status: Completed
        """,
        
        'Fidelity Bank': """
        FIDELITY BANK
        Transaction Alert
        
        Date: 25-01-2025
        From: Mike Johnson 1122334455
        To: Nancy Davis 5544332211
        
        Amount: NGN 35,000.00
        Transaction Type: Transfer
        Reference: FID123456
        """,
        
        'Stanbic IBTC': """
        STANBIC IBTC
        Transaction Receipt
        
        Date: 30/01/2025
        Account: 1234567890
        
        Sender: Oliver Wilson
        Recipient: Patricia Brown
        Amount: ₦80,000.00
        
        Type: Credit
        Status: Successful
        """,
        
        'Moniepoint': """
        Moniepoint
        Transaction Details
        
        Date: 05/02/2025
        From: Queen Elizabeth 08012345678
        To: Robert Smith 08087654321
        
        Amount: ₦40,000.00
        Transaction: Sent
        Status: Completed
        
        Thank you for using Moniepoint
        """,
        
        'Kuda Bank': """
        Kuda Bank
        Transaction Receipt
        
        Date: 10/02/2025
        Account: 9876543210
        
        Sender: Sarah Johnson
        Recipient: Tom Wilson
        Amount: ₦55,000.00
        
        Type: Transfer
        Status: Successful
        """
    }
    
    print("🧪 Testing Enhanced OCR System for Nigerian Banks")
    print("=" * 60)
    
    for bank_name, receipt_text in sample_receipts.items():
        print(f"\n🏦 Testing {bank_name}")
        print("-" * 40)
        
        # Test bank detection
        bank_key, bank_config = detect_bank(receipt_text)
        print(f"Detected Bank: {bank_config['name']}")
        
        # Test transaction type detection
        transaction_type = detect_transaction_type_enhanced(receipt_text, bank_config)
        print(f"Transaction Type: {transaction_type}")
        
        # Test data extraction (simulating OCR output)
        # Since we don't have actual image files, we'll simulate the OCR text
        extracted_data = {
            "amount": None,
            "sender": None,
            "receiver": None,
            "account_number": None,
            "bank": bank_config['name'],
            "notes": receipt_text,
            "transaction_date": None
        }
        
        # Extract data using our functions
        from Tracker.utils import extract_amount, extract_sender_receiver, extract_account_number, extract_datetime_enhanced
        
        extracted_data["amount"] = extract_amount(receipt_text, bank_config)
        extracted_data["sender"], extracted_data["receiver"] = extract_sender_receiver(receipt_text, bank_config)
        extracted_data["account_number"] = extract_account_number(receipt_text, bank_config)
        extracted_data["transaction_date"] = extract_datetime_enhanced(receipt_text, bank_config)
        
        # Display results
        print(f"Amount: ₦{extracted_data['amount']:,}" if extracted_data['amount'] else "Amount: Not detected")
        print(f"Sender: {extracted_data['sender']}" if extracted_data['sender'] else "Sender: Not detected")
        print(f"Receiver: {extracted_data['receiver']}" if extracted_data['receiver'] else "Receiver: Not detected")
        print(f"Account: {extracted_data['account_number']}" if extracted_data['account_number'] else "Account: Not detected")
        print(f"Date: {extracted_data['transaction_date']}" if extracted_data['transaction_date'] else "Date: Not detected")
        
        # Overall assessment
        success_count = sum([
            1 if extracted_data['amount'] else 0,
            1 if extracted_data['sender'] or extracted_data['receiver'] else 0,
            1 if extracted_data['transaction_date'] else 0,
            1 if transaction_type else 0
        ])
        
        if success_count >= 3:
            print("✅ Good extraction")
        elif success_count >= 2:
            print("⚠️  Partial extraction")
        else:
            print("❌ Poor extraction")

def test_with_actual_image(image_path):
    """
    Test OCR with an actual image file
    """
    if not os.path.exists(image_path):
        print(f"❌ Image file not found: {image_path}")
        return
    
    print(f"\n🖼️  Testing with actual image: {image_path}")
    print("-" * 50)
    
    try:
        extracted_data = extract_transaction_data(image_path)
        
        print(f"Bank: {extracted_data.get('bank', 'Unknown')}")
        print(f"Amount: ₦{extracted_data.get('amount', 0):,}" if extracted_data.get('amount') else "Amount: Not detected")
        print(f"Sender: {extracted_data.get('sender', 'Not detected')}")
        print(f"Receiver: {extracted_data.get('receiver', 'Not detected')}")
        print(f"Account: {extracted_data.get('account_number', 'Not detected')}")
        print(f"Date: {extracted_data.get('transaction_date', 'Not detected')}")
        
        # Test transaction type detection
        bank_key, bank_config = detect_bank(extracted_data.get('notes', ''))
        transaction_type = detect_transaction_type_enhanced(extracted_data.get('notes', ''), bank_config)
        print(f"Transaction Type: {transaction_type}")
        
    except Exception as e:
        print(f"❌ Error processing image: {str(e)}")

if __name__ == "__main__":
    print("🚀 OCR Testing Tool for Tracklytic")
    print("=" * 50)
    
    # Test with sample data
    test_ocr_with_sample_data()
    
    # Test with actual image if provided
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
        test_with_actual_image(image_path)
    else:
        print("\n💡 To test with an actual image, run:")
        print("python test_ocr.py path/to/your/receipt.jpg")
    
    print("\n✅ Testing completed!")
