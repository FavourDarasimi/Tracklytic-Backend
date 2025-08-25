# Enhanced OCR System for Nigerian Banks

## Overview

The enhanced OCR (Optical Character Recognition) system has been completely rewritten to handle receipts from multiple Nigerian banks with high accuracy. The system now supports 13 major Nigerian banks and financial institutions.

## Supported Banks

### Traditional Banks
1. **GTBank** - Guaranty Trust Bank
2. **Access Bank** 
3. **Zenith Bank**
4. **First Bank** - First Bank of Nigeria
5. **UBA** - United Bank for Africa
6. **Ecobank**
7. **Fidelity Bank**
8. **Stanbic IBTC**
9. **Polaris Bank**

### Digital Banks & Fintech
10. **OPay**
11. **PalmPay**
12. **Moniepoint**
13. **Kuda Bank**

## Key Features

### 🏦 Bank-Specific Detection
- Automatically detects which bank the receipt is from
- Uses bank-specific keywords and patterns
- Adapts parsing logic based on detected bank

### 💰 Enhanced Amount Extraction
- Multiple regex patterns for different amount formats
- Handles ₦, $, NGN currency symbols
- Supports comma-separated numbers (e.g., ₦50,000.00)
- Decimal point handling

### 👥 Improved Sender/Receiver Detection
- Bank-specific patterns for sender and receiver fields
- Handles different field names (From/To, Sender/Recipient, etc.)
- Account number extraction and cleaning
- Name cleaning and formatting

### 📅 Advanced Date Parsing
- Multiple date formats support
- DD/MM/YYYY, DD-MM-YYYY formats
- Text-based dates (e.g., "15 Jan 2024")
- Timezone handling

### 🔄 Transaction Type Detection
- Bank-specific keywords for debit/credit detection
- Enhanced logic for transfer types
- Fallback mechanisms for unknown formats

## Technical Implementation

### Bank Configuration Structure

Each bank has a configuration object with:

```python
{
    'name': 'Bank Name',
    'keywords': ['bank', 'keywords', 'for', 'detection'],
    'amount_patterns': [regex_patterns],
    'sender_patterns': [regex_patterns],
    'receiver_patterns': [regex_patterns],
    'account_patterns': [regex_patterns],
    'date_patterns': [regex_patterns],
    'transaction_type_keywords': {
        'debit': ['keywords'],
        'credit': ['keywords']
    }
}
```

### Core Functions

#### `detect_bank(text)`
- Analyzes receipt text to identify the bank
- Returns bank key and configuration
- Falls back to generic patterns if no bank detected

#### `extract_amount(text, bank_config)`
- Uses bank-specific patterns to extract amounts
- Handles multiple currency formats
- Cleans and validates extracted amounts

#### `extract_sender_receiver(text, bank_config)`
- Extracts sender and receiver information
- Uses bank-specific field patterns
- Cleans account numbers from names

#### `extract_datetime_enhanced(text, bank_config)`
- Parses dates using bank-specific formats
- Handles multiple date styles
- Returns timezone-aware datetime objects

#### `detect_transaction_type_enhanced(text, bank_config, user_name)`
- Determines transaction type using bank keywords
- Enhanced logic for transfer detection
- Fallback to legacy methods if needed

## API Usage

### Upload Receipt Endpoint

**URL:** `POST /transaction/upload/receipt/`

**Request:**
```http
POST /transaction/upload/receipt/
Content-Type: multipart/form-data

receipt: [image file]
```

**Response:**
```json
{
    "status": "success",
    "message": "Transaction data extracted successfully from GTBank",
    "data": {
        "id": 123,
        "user": "username",
        "party_name": "Jane Smith",
        "amount": 50000,
        "type": "Expense",
        "transaction_date": "2024-12-15T14:30:25Z",
        "notes": "Bank: GTBank\nAccount: 1234567890\n[OCR text]",
        "receipt": "/media/receipts/receipt.jpg"
    },
    "extracted_info": {
        "bank": "GTBank",
        "account_number": "1234567890",
        "sender": "John Doe",
        "receiver": "Jane Smith",
        "detected_type": "Expense"
    }
}
```

## Testing

### Test Script

Run the test script to verify OCR functionality:

```bash
# Test with sample data
python test_ocr.py

# Test with actual image
python test_ocr.py path/to/receipt.jpg
```

### Sample Test Output

```
🧪 Testing Enhanced OCR System for Nigerian Banks
============================================================

🏦 Testing GTBank
----------------------------------------
Detected Bank: GTBank
Transaction Type: Expense
Amount: ₦50,000
Sender: John Doe
Receiver: Jane Smith
Account: 1234567890
Date: 2024-12-15 14:30:25+00:00
✅ Good extraction
```

## Error Handling

### File Validation
- Supports JPG, JPEG, PNG, PDF formats
- Validates file extensions
- Returns clear error messages for unsupported formats

### OCR Processing
- Graceful handling of OCR failures
- Fallback mechanisms for data extraction
- Comprehensive error reporting

### Data Validation
- Validates extracted amounts
- Ensures required fields are present
- Provides detailed error messages

## Performance Optimizations

### EasyOCR Configuration
- Single reader instance for all requests
- Optimized for English text recognition
- Efficient image processing

### Pattern Matching
- Compiled regex patterns for faster matching
- Bank-specific pattern optimization
- Efficient text processing

## Supported File Formats

- **Images:** JPG, JPEG, PNG
- **Documents:** PDF (converted to images)
- **Size:** Recommended under 10MB for optimal performance

## Best Practices

### Image Quality
- Ensure good lighting when taking photos
- Avoid blurry or tilted images
- Use high-resolution images when possible

### Receipt Format
- Capture the entire receipt
- Ensure text is clearly visible
- Avoid covering important information

### Testing
- Test with various bank receipts
- Verify extracted data accuracy
- Use the test script for validation

## Troubleshooting

### Common Issues

1. **Amount not detected**
   - Check if amount format matches bank patterns
   - Ensure currency symbol is visible
   - Verify image quality

2. **Bank not detected**
   - Check if bank name is clearly visible
   - Verify bank keywords in configuration
   - System will use generic patterns as fallback

3. **Date parsing issues**
   - Ensure date format is supported
   - Check for clear date text
   - Verify date patterns in bank configuration

### Debug Mode

Enable debug logging to see detailed extraction process:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Future Enhancements

### Planned Features
- Support for more Nigerian banks
- Machine learning-based pattern recognition
- Receipt template learning
- Multi-language support
- Real-time processing optimization

### Bank Addition Process

To add a new bank:

1. Add bank configuration to `BANK_PATTERNS`
2. Define bank-specific keywords
3. Create regex patterns for data extraction
4. Test with sample receipts
5. Update documentation

## Dependencies

- **EasyOCR:** OCR engine for text extraction
- **pdf2image:** PDF to image conversion
- **Django:** Web framework
- **Pillow:** Image processing
- **NumPy:** Numerical operations

## License

This OCR system is part of the Tracklytic project and follows the same licensing terms.
