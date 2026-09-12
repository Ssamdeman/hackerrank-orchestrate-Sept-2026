# Image Financial Value Extraction

Reconnaissance and manual transcription of financial evidence from the 16 PNG documents in `dataset/media/images/`.

Each image corresponds to a single row in `dataset/images.csv` and fills a blank `amount` field in `dataset/financial_events.csv`.

---

## image_01
**File:** dataset/media/images/image_01.png  
**Event:** event_253 | user_03 | request_03  
**Event description:** August 2019 net salary  
**Expected currency:** IDR  
**Document type:** payroll letter  
**EXTRACTED AMOUNT:** 4,365,000  
**Currency on document:** IDR  
**Date on document:** 2 Sep 2019 (Printed on: 2 Sep 2019 09:35 PM; Period: Aug-2019)  
**Found at:** bottom-right of summary table, row labelled "Net Pay"  
**Subtotal / Tax / Total breakdown:**
- Subtotal Earnings: 4,780,800
- Total Earnings: 4,780,800
- Subtotal Deductions: 415,800
- Total Deductions: 415,800
- Tax Allowance: 0
- Tax Borne by Company: 0
- Tax Penalty Borne By Company: 0
- Tax: 0
- Tax Penalty: 0
- Net Pay: 4,365,000  
*Selection rationale:* Selected 4,365,000 because the event description specifies "August 2019 net salary" (the take-home pay transferred to bank account after deductions).  
**Other values:** Employee No. 19050378 | Tax Ref No 899763619907000 | Salary 4,500,000 | Allowance BPJS Pen 2% Company 90,000 | Allowance JHT 3.7% 166,500 | Allowance JKK 0.24% 10,800 | Allowance JKM 0.3% 13,500 | Deduction BPJS Pen 2% Company 90,000 | Deduction BPJS Pen 1% Employee 45,000 | Deduction JHT 3.7% 166,500 | Deduction JHT 2% Employee 90,000 | Deduction JKK 0.24% 10,800 | Deduction JKM 0.3% 13,500 | Account No. 2582373290  
**Confidence:** clear  
**Notes:** Bank Central Asia transfer line confirms: "IDR 4,365,000". Amount in words: "Four Million Three Hundred Sixty Five Thousand Rupiahs".

---

## image_02
**File:** dataset/media/images/image_02.png  
**Event:** event_1442 | user_16 | request_16  
**Event description:** Outstanding rent balance  
**Expected currency:** INR  
**Document type:** receipt  
**EXTRACTED AMOUNT:** 1,00,000.00  
**Currency on document:** Rupees (body text) / Rs. (footer note)  
**Date on document:** 11/08/23  
**Found at:** middle-right table section, row labelled "Balance Due:"  
**Subtotal / Tax / Total breakdown:**
- Rent & Maintanance: 1,80,000.00
- Water Charges: 5,000.00
- Rental Tax: 5,000.00
- Electrical Charges: 10,000.00
- Total Amount to be Received: 2,00,000.00
- Amount Received: 1,00,000.00
- Balance Due: 1,00,000.00  
*Selection rationale:* Selected 1,00,000.00 because the event description explicitly designates "Outstanding rent balance" (Balance Due).  
**Other values:** Receipt No. 9453 | Tenant Yashwant sum of Rupees 2,00,000 | Address PIN 560102 | Address PIN 560076 | Phone No. 9999999000 | Note threshold 1 Lakh | Note threshold Rs.5000  
**Confidence:** clear  
**Notes:** Document is titled "Rent Receipt". Footer notes mention tax thresholds: "1. PAN of Owner not mandatory( In case your annual rent payment does not exceed 1 Lakh", "2. Revenue stamp necessary for Transaction more than Rs.5000".

---

## image_03
**File:** dataset/media/images/image_03.png  
**Event:** event_1545 | user_17 | request_17  
**Event description:** Bulk groceries and pantry purchase  
**Expected currency:** INR  
**Document type:** receipt  
**EXTRACTED AMOUNT:** 41272.00  
**Currency on document:** UNREADABLE (no currency symbol printed; implicit INR from Bangalore GSTIN 29ALCPJ4001H1ZI)  
**Date on document:** 27/02/2026 (timestamp: 16:10 PM)  
**Found at:** bottom-right, rows labelled "Net Amount:" (41272.0) and "Cash Paid:" (41272.00)  
**Subtotal / Tax / Total breakdown:**
- Line item total: 41272.00
- Tax: UNREADABLE (no tax broken out on Bill of Supply)
- Net Amount: 41272.0
- Cash Paid: 41272.00  
*Selection rationale:* Selected 41272.00 as the settled total cash paid for the pantry order.  
**Other values:** Address PIN 560095 | Phone 9342823271 | Bill No 1125000158 | Item 1 (Coke Die..): Qty 5PC, MRP 1160.00, SP 1160.00, Amt 5800.00 | Item 2 (pulpy or..): Qty 1PC, MRP 750.00, SP 750.00, Amt 750.00 | Item 3 (the whol..): Qty 29PC, MRP 480.00, SP 480.00, Amt 13920.00 | Item 4 (Rite Bit..): Qty 10PC, MRP 480.00, SP 480.00, Amt 4800.00 | Item 5 (Ocean Fr..): Qty 1PC, MRP 2500.00, SP 2500.00, Amt 2500.00 | Item 6 (ferrero ..): Qty 8PC, MRP 269.00, SP 269.00, Amt 2152.00 | Item 7 (munch): Qty 3PC, MRP 250.00, SP 250.00, Amt 750.00 | Item 8 (5 star): Qty 2PC, MRP 270.00, SP 270.00, Amt 540.00 | Item 9 (dark fan..): Qty 5PC, MRP 338.00, SP 338.00, Amt 1690.00 | Item 10 (Butter ..): Qty 9PC, MRP 810.00, SP 810.00, Amt 7290.00 | Item 11 (dairy m..): Qty 3PC, MRP 360.00, SP 360.00, Amt 1080.00 | Items/Qty: 11/76  
**Confidence:** clear  
**Notes:** Faint blue rectangular watermark stamp across middle reading "INWARD ... 28 FEB ...".

---

## image_04
**File:** dataset/media/images/image_04.png  
**Event:** event_1700 | user_19 | request_19  
**Event description:** Delivered grocery order  
**Expected currency:** INR  
**Document type:** receipt  
**EXTRACTED AMOUNT:** 2854.00  
**Currency on document:** ₹  
**Date on document:** UNREADABLE (no date printed in screenshot)  
**Found at:** bottom-right, row labelled "Item Bill" under "TOTAL ORDER BILL DETAILS"  
**Subtotal / Tax / Total breakdown:**
- Item Bill (subtotal): ₹2854.00
- Taxes / Delivery Fee / Final Total: UNREADABLE (cropped off at bottom; partial line below Item Bill shows "D... ₹16...")  
*Selection rationale:* Selected ₹2854.00 because it is the only complete visible billing amount on the receipt; subsequent fee/tax/total lines are cut off at the bottom border.  
**Other values:** 13 items | 1 x Nissin Cup Noodles Mazedaar Masala: ₹95.0 | 1 x The Whole Truth 20G Protein Bars: ₹531.0 | 1 x Flyer - Nubu: ₹0 | 1 x The Whole Truth 13G Protein Millet Bar: ₹186.0 | 1 x O'Cean Fruit Water Mango & Passion: ₹122.0 | 2 x The Whole Truth Double Cocoa Prote...: ₹464.0 | 1 x The Whole Truth Almond Choco Fudg...: ₹184.0 | 3 x Nissin Cup Noodles Mazedaar Masala: ₹144.0 | 3 x Wickedgud Instant Masala Cup Noodles: ₹75.0 | 3 x O'Cean Peach & Passion Fruit Juice...: ₹366.0 | 1 x The Whole Truth Protein Bar Orange...: ₹190.0 | 1 x The Whole Truth Protein Bar Hazelnut Cocoa No...: ₹121.0 | 2 x Nissin Cup Noodles Spiced Chicken: ₹376.0 | Cropped line below Item Bill: ₹16.00  
**Confidence:** partly obscured  
**Notes:** The image is truncated at the lower boundary. Grand total order bill is cropped out, but Item Bill (₹2854.00) matches the sum of the 13 line items.

---

## image_05
**File:** dataset/media/images/image_05.png  
**Event:** event_1786 | user_20 | request_20  
**Event description:** Outstanding telecom bill  
**Expected currency:** INR  
**Document type:** bill  
**EXTRACTED AMOUNT:** 704.05  
**Currency on document:** ₹ (and "Rupees and Five Paise" in words)  
**Date on document:** 06-Feb-2026 (due date printed twice)  
**Found at:** left card row labelled "Amount due till 06-Feb-2026 = 704.05" and right card row labelled "Total (₹) 704.05"  
**Subtotal / Tax / Total breakdown:**
- Rentals: 580.65
- Usage charges: 16.00
- Taxes: 107.40
- Total (₹): 704.05
- This month's charges: 704.05
- Previous balance: 3,543.54
- Payments: - 3,543.54
- Amount due till 06-Feb-2026: 704.05
- Amount due after 06-Feb-2026: 822.05  
*Selection rationale:* Selected 704.05 because it is "This month's charges" / "Total (₹)" and the amount due on or before the due date (previous balance was fully settled).  
**Other values:** Previous balance 3,543.54 | Payments - 3,543.54 | Rentals 580.65 | Usage charges 16.00 | Taxes 107.40 | Amount due after 06-Feb-2026 822.05  
**Confidence:** clear  
**Notes:** Banner at bottom displays promotional text: "Now view, download and pay your bills anytime, anywhere! Payments now made easier with Airtel Thanks for Business! Visit airtel.in/business/thanksforbusiness/".

---

## image_06
**File:** dataset/media/images/image_06.png  
**Event:** event_3051 | user_33 | request_33  
**Event description:** Grocery tax invoice  
**Expected currency:** INR  
**Document type:** invoice  
**EXTRACTED AMOUNT:** 1995.00  
**Currency on document:** INR (in column headers CGST (INR), SGST (INR)) / Rupees (in words)  
**Date on document:** UNREADABLE (no date printed on this crop of the invoice)  
**Found at:** bottom-right cell in table row labelled "Total"  
**Subtotal / Tax / Total breakdown:**
- Taxable Value subtotal: 1,899.98
- CGST (INR): 47.49
- SGST (INR): 47.49
- Total: 1995.00  
*Selection rationale:* Selected 1995.00 as the final invoice Total, verified by Amount in Words "One Thousand And Nine Hundred And Ninety-Five Rupees And Zero Paisa Only".  
**Other values:** Total Qty 7 | CGST (INR) 47.49 | SGST (INR) 47.49 | Total 1995.00 | Item 1: MRP 310.00, Disc 27.50, Qty 2, Taxable 538.10, CGST 2.5% 13.45, SGST 2.5% 13.45, Total 565.00; Delivery charge: Taxable 2.98, CGST 0.07, SGST 0.07, Total 3.13 | Item 2: MRP 310.00, Disc 34.00, Qty 2, Taxable 525.71, CGST 2.5% 13.14, SGST 2.5% 13.14, Total 552.00; Delivery charge: Taxable 2.91, CGST 0.07, SGST 0.07, Total 3.06 | Item 3: MRP 310.00, Disc 21.00, Qty 1, Taxable 275.24, CGST 2.5% 6.88, SGST 2.5% 6.88, Total 289.00; Delivery charge: Taxable 1.53, CGST 0.04, SGST 0.04, Total 1.60 | Item 4: MRP 310.00, Disc 21.00, Qty 1, Taxable 275.24, CGST 2.5% 6.88, SGST 2.5% 6.88, Total 289.00; Delivery charge: Taxable 1.53, CGST 0.04, SGST 0.04, Total 1.60 | Item 5: MRP 310.00, Disc 21.00, Qty 1, Taxable 275.24, CGST 2.5% 6.88, SGST 2.5% 6.88, Total 289.00; Delivery charge: Taxable 1.53, CGST 0.04, SGST 0.04, Total 1.60 | UPCs: 8906143890497, 8906143890473, 8906143890480, 8906143890527 | HSN 18069010 | FSSAI 10018064001545  
**Confidence:** clear  
**Notes:** Header with invoice number and date was not included in this document image crop.

---

## image_07
**File:** dataset/media/images/image_07.png  
**Event:** event_3231 | user_35 | request_35  
**Event description:** Restaurant tax invoice  
**Expected currency:** INR  
**Document type:** receipt  
**EXTRACTED AMOUNT:** 8528  
**Currency on document:** (RS)  
**Date on document:** 29-10-2025 (timestamp: 12:12 PM)  
**Found at:** bottom line labelled "Grand Total (RS) : 8528"  
**Subtotal / Tax / Total breakdown:**
- SubTotal: 8122.00
- SGST 2.50 %: 203.05
- CGST 2.50 %: 203.05
- Total: 8528.10
- Grand Total (RS): 8528  
*Selection rationale:* Selected 8528 because it is the final payable rounded Grand Total printed on the bill (unrounded Total is 8528.10).  
**Other values:** Token No 1 | BillNo 10 | Table P1 | Covers 1 | TEL 080-40996000, 65316000 | GSTIN 29AACFA1961A1ZY | FSSAI No 11217334001482 | Carrier Meals: Qty 5.0, Rate 580.0, Amt 2900.00 | Parcel Charges: Qty 5.0, Rate 90.0, Amt 450.00 | Chicken Nagarjuna: Qty 6.0, Rate 415.0, Amt 2490.00 | Chapathi: Qty 30.0, Rate 60.0, Amt 1800.00 | Dal: Qty 2.0, Rate 155.0, Amt 310.00 | Big Container: Qty 2.0, Rate 15.0, Amt 30.00 | Container Small: Qty 8.0, Rate 12.0, Amt 96.00 | Packing (Large): Qty 2.0, Rate 23.0, Amt 46.00  
**Confidence:** clear  
**Notes:** Blue "PAID" stamp at top of receipt.

---

## image_08
**File:** dataset/media/images/image_08.png  
**Event:** event_4535 | user_48 | request_48  
**Event description:** Property maintenance invoice  
**Expected currency:** INR  
**Document type:** receipt  
**EXTRACTED AMOUNT:** 15,339.00  
**Currency on document:** ₹ (table/banner) / Rs (fee) / Rupees (in words)  
**Date on document:** 24-07-2026 (Charge Date; Due Date: 30-08-2026)  
**Found at:** dark green banner row labelled "Total Amount Received ₹ 15,339.00"  
**Subtotal / Tax / Total breakdown:**
- Maintenance charge: 13,880.00
- Club House Charges: 1,050.00
- Infrastructure Expenses: 409.00
- Total Amount Received: 15,339.00
- Convenience Fee: 0.00  
*Selection rationale:* Selected 15,339.00 as it is the Total Amount Received, matching the Amount in Words "Rupees Fifteen Thousand Three Hundred Thirty Nine Only".  
**Other values:** Invoice No. 6455 | SQFT 1720.0 | Rate per SQFT 8.07 | Months 3 | Convenience Fee Rs 0.00 | Transaction ID 0ec470dedc1c455ab42f58e9c7729305 | Charged Amounts: 13,880.00, 1,050.00, 409.00  
**Confidence:** clear  
**Notes:** Online payment receipt via paytm.

---

## image_09
**File:** dataset/media/images/image_09.png  
**Event:** event_5170 | user_55 | request_55  
**Event description:** Water bill due  
**Expected currency:** INR  
**Document type:** bill  
**EXTRACTED AMOUNT:** 723.00  
**Currency on document:** ₹ (table/banner) / Rs (fee) / Rupees (in words)  
**Date on document:** 07-06-2026 (Charge Date; Due Date: 02-07-2026)  
**Found at:** dark green banner row labelled "Total Amount Received ₹ 723.00"  
**Subtotal / Tax / Total breakdown:**
- Charged Amount(₹): 723.00
- Amount (₹): 723.00
- Total Amount Received: 723.00  
*Selection rationale:* Selected 723.00 because it is the Total Amount Received, verified by Amount in Words "Rupees Seven Hundred Twenty Three Only".  
**Other values:** Invoice No. 6320 | Convenience Fee Rs 0.00 | Transaction ID 39350810ed9045da91798478b89ca561  
**Confidence:** clear  
**Notes:** Online payment receipt via paytm for Jan to March 2026 Water Bill.

---

## image_10
**File:** dataset/media/images/image_10.png  
**Event:** event_6033 | user_64 | request_64  
**Event description:** Large grocery tax invoice  
**Expected currency:** INR  
**Document type:** invoice  
**EXTRACTED AMOUNT:** 79,679.26  
**Currency on document:** ₹ (Total and Balance Due) / Indian Rupee (in words)  
**Date on document:** UNREADABLE (metadata strip between pages is blacked-out/illegible)  
**Found at:** bottom-right corner, rows labelled "Total ₹79,679.26" and "Balance Due ₹79,679.26"  
**Subtotal / Tax / Total breakdown:**
- Sub Total: 72,045.00
- CGST2.5 (2.5%): 1,513.13
- SGST2.5 (2.5%): 1,513.13
- CGST20 (20%): 2,304.00
- SGST20 (20%): 2,304.00
- Total: 79,679.26
- Balance Due: 79,679.26  
*Selection rationale:* Selected 79,679.26 as the grand Total / Balance Due, matching the verbatim words "Indian Rupee Seventy-Nine Thousand Six Hundred Seventy-Nine and Twenty-Six Paise Only".  
**Other values:** 22 line items total | Line item amounts: 1,425.00, 1,000.00, 6,480.00, 6,480.00, 480.00, 2,250.00, 9,600.00, 1,920.00, 2,880.00, 480.00, 2,400.00, 2,250.00, 400.00, 3,120.00, 4,520.00, 4,320.00, 4,800.00, 4,800.00, 4,800.00, 3,720.00, 2,680.00, 1,240.00 | Quantities: 15.00, 10.00, 240.00, 240.00, 48.00, 90.00, 240.00, 48.00, 72.00, 12.00, 60.00, 90.00, 10.00, 48.00, 40.00, 27.00, 60.00, 60.00, 60.00, 12.00, 8.00, 4.00 | Rates: 95.00, 100.00, 27.00, 27.00, 10.00, 25.00, 40.00, 40.00, 40.00, 40.00, 40.00, 25.00, 40.00, 65.00, 113.00, 160.00, 80.00, 80.00, 80.00, 310.00, 335.00, 310.00 | Sub Total 72,045.00 | CGST2.5 1,513.13 | SGST2.5 1,513.13 | CGST20 2,304.00 | SGST20 2,304.00  
**Confidence:** clear  
**Notes:** The two pages of the invoice are stitched together with a dark separator band across the middle. Customer notes: "Thanks for your business.".

---

## image_11
**File:** dataset/media/images/image_11.png  
**Event:** event_6859 | user_73 | request_73  
**Event description:** Hospital bill payable  
**Expected currency:** INR  
**Document type:** bill  
**EXTRACTED AMOUNT:** 3650.00  
**Currency on document:** UNREADABLE (no currency symbol printed; hospital located in Pune, India)  
**Date on document:** 19-Jan-2023 (Date); 18-Jan-2023, 12:19 PM (Admission Date)  
**Found at:** middle-right section under PROVISIONAL BILL summary, row labelled "Total Bill Amount: 3650.00" / "Amount Payable: 3650.00"  
**Subtotal / Tax / Total breakdown:**
- Room & Nursing Charges: 1650.00
- OT Charges: 1000.00
- Professional Fees: 1000.00
- Total Bill Amount: 3650.00
- Amount Payable: 3650.00
- Amount Paid: 0.00
- Balance: 3650.00  
*Selection rationale:* Selected 3650.00 as it is the Total Bill Amount / Amount Payable / Balance due for hospital services.  
**Other values:** Patient UID 1 | Age 22 years | Contact No 9403265989 | PIN 411056, 411051 | Admission No 000001 | Reg. No. DR86486 | Phone 08208064299 | Primary Code 100000: 1650.00 | Primary Code 300000: 1000.00 | Primary Code 500000: 1000.00 | Detailed Breakup Subtotals: Bed Charges 250.00, Nursing Charges 1400.00, OT Charges 1000.00, Professional Fees 500.00  
**Confidence:** clear  
**Notes:** Titled "PROVISIONAL BILL". "Paid amount in words : Zero".

---

## image_12
**File:** dataset/media/images/image_12.png  
**Event:** event_7307 | user_78 | request_78  
**Event description:** Taxi fare  
**Expected currency:** USD  
**Document type:** receipt  
**EXTRACTED AMOUNT:** 33.50  
**Currency on document:** $  
**Date on document:** 01/10/2025 21:45  
**Found at:** lower-middle, bold row labelled "Total: $33.50"  
**Subtotal / Tax / Total breakdown:**
- Ride Distance (12.3 miles): $28.50
- Airport Surcharge: $5.00
- Subtotal: $33.50
- Tax: $0.00
- Total: $33.50  
*Selection rationale:* Selected $33.50 as the total taxi fare charged.  
**Other values:** Ride Distance $28.50 | Airport Surcharge $5.00 | Subtotal $33.50 | Tax $0.00 | Cash Paid $40.00 | Change $6.50 | Distance 12.3 mi / miles | License #TC-5567 | Dispatch (555) 567-8901 | Trip #CC-8923 | Vehicle #142 | Barcode 892320251001  
**Confidence:** clear  
**Notes:** Document includes CityCab Service logo and a barcode at bottom.

---

## image_13
**File:** dataset/media/images/image_13.png  
**Event:** event_7941 | user_84 | request_84  
**Event description:** Tote bag order  
**Expected currency:** INR  
**Document type:** receipt  
**EXTRACTED AMOUNT:** 2298  
**Currency on document:** ₹  
**Date on document:** UNREADABLE (no date printed in screenshot)  
**Found at:** bottom-right, row labelled "Total paid"  
**Subtotal / Tax / Total breakdown:**
- Item Total (2 items): ₹2298
- Delivery: Free
- Total paid: ₹2298  
*Selection rationale:* Selected 2298 because it represents the "Total paid" inclusive of taxes and delivery.  
**Other values:** DailyObjects Mumbai City Tote Bag (1 unit): ₹699 | Ivory - Navy All Time Tote Bag (1 unit): ₹1,599 | Item Total (2 items): ₹2298  
**Confidence:** clear  
**Notes:** E-commerce order checkout summary screen. Subtitle under Total paid states: "Incl. taxes and delivery".

---

## image_14
**File:** dataset/media/images/image_14.png  
**Event:** event_9421 | user_101 | request_101  
**Event description:** Pharmacy purchase  
**Expected currency:** INR  
**Document type:** bill  
**EXTRACTED AMOUNT:** 4543.00  
**Currency on document:** Rs. Ps.  
**Date on document:** UNREADABLE (header containing date is cropped out)  
**Found at:** bottom-right box labelled "TOTAL 4543.00"  
**Subtotal / Tax / Total breakdown:**
- Line item total: 4543.00
- Taxes: UNREADABLE (footer states "Prices Charged Include all Taxes")
- TOTAL: 4543.00  
*Selection rationale:* Selected 4543.00 as the handwritten grand TOTAL, matching the sum of all itemized lines (1500 + 724 + 796 + 550 + 303 + 670 = 4543).  
**Other values:** Item 1 (Samahan): Qty 2, Amount 1500.00 | Item 2 (moov spray): Qty 2, Amount 724.00 | Item 3 (Axe oil): Qty 1, Amount 796.00 | Item 4 (stayfree): Qty 2, Amount 550.00 | Item 5 (Benadryl): Amount 303.00 | Item 6: Amount 670.00  
**Confidence:** clear  
**Notes:** Handwritten physical pharmacy receipt. Top header area (store name, bill date, bill number) is cropped.

---

## image_15
**File:** dataset/media/images/image_15.png  
**Event:** event_9806 | user_105 | request_105  
**Event description:** Airline ticket purchase  
**Expected currency:** INR  
**Document type:** invoice  
**EXTRACTED AMOUNT:** 9,968.00  
**Currency on document:** INR  
**Date on document:** 07-Jun-2026  
**Found at:** bottom-right cell in Grand Total table row, labelled "Total(Incl Taxes)"  
**Subtotal / Tax / Total breakdown:**
- Taxable Value: 9,124.00
- NonTaxable/Exempted Value: 388.00
- Total (before tax): 9,512.00
- IGST Amount: 0.00
- CGST Amount: 228.00
- SGST/UGST Amount: 228.00
- CESS Amount: 0.00
- Total(Incl Taxes): 9,968.00  
*Selection rationale:* Selected 9,968.00 as it is the final grand Total(Incl Taxes) for the airline ticket.  
**Other values:** SAC Code 996425 | Air Travel and related charges Total(Incl Taxes) 9,580.00 | Airport Charges 388.00 | Flight No 6E - 861 | PNR UC83TT | CGST Tax % 2.50 | SGST/UGST Tax % 2.50 | Rule 48 year reference: 2017-18  
**Confidence:** clear  
**Notes:** InterGlobe Aviation Limited (IndiGo) tax invoice. Includes passenger itinerary terms 1 through 9.

---

## image_16
**File:** dataset/media/images/image_16.png  
**Event:** event_10521 | user_113 | request_113  
**Event description:** EV charging wallet payment  
**Expected currency:** INR  
**Document type:** invoice  
**EXTRACTED AMOUNT:** 393.22  
**Currency on document:** UNREADABLE (no symbol next to figures; "Rupees And Twenty Two Paise" in words)  
**Date on document:** 03/09/2026, 12:35:10 am  
**Found at:** bottom-right of table, row labelled "Total 393.22"  
**Subtotal / Tax / Total breakdown:**
- Base Energy Delivered Amount: 333.24
- Session Fee: -
- Idle Fee: -
- CGST 9 %: 29.99
- SGST 9 %: 29.99
- Total: 393.22  
*Selection rationale:* Selected 393.22 as it is the final invoice Total, verified by Amount in Words "Three Hundred and Ninety Three Rupees And Twenty Two Paise Only".  
**Other values:** HSN CODE 996749 | ENERGY DELIVERED 12.58 kWh | TARIFF 26.49 /kWh | DURATION 00:15:26 | CHARGE POINT 1110 | CGST 9% 29.99 | SGST 9% 29.99  
**Confidence:** clear  
**Notes:** Computer-generated invoice. Payment method noted as WALLET.

---

## Summary Table

| image_id | event_id | amount | confidence |
| :--- | :--- | :--- | :--- |
| image_01 | event_253 | 4,365,000 | clear |
| image_02 | event_1442 | 10,0000.00 | clear |
| image_03 | event_1545 | 41272.00 | clear |
| image_04 | event_1700 | 2854.00 | partly obscured |
| image_05 | event_1786 | 704.05 | clear |
| image_06 | event_3051 | 1995.00 | clear |
| image_07 | event_3231 | 8528 | clear |
| image_08 | event_4535 | 15,339.00 | clear |
| image_09 | event_5170 | 723.00 | clear |
| image_10 | event_6033 | 79,679.26 | clear |
| image_11 | event_6859 | 3650.00 | clear |
| image_12 | event_7307 | 33.50 | clear |
| image_13 | event_7941 | 2298 | clear |
| image_14 | event_9421 | 4543.00 | clear |
| image_15 | event_9806 | 9,968.00 | clear |
| image_16 | event_10521 | 393.22 | clear |
