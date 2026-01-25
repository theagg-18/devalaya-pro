# Implementation Plan: Malayalam Calendar & Star Integration

This plan outlines how to integrate an automated Malayalam Star (Nakshatra) calculator into the Devalaya Billing System. 
It supports two key features:
1.  **Date -> Star**: Auto-detect the Star for a selected date.
2.  **Star -> Date (Booking)**: Find the next occurrence dates for a specific star (e.g., "When is the next Rohini?").

## 1. Technical Approach
We will use an **Offline Astronomical Calculation** approach. This ensures the system works without an internet connection (unlike API-based solutions) and is faster.

**Core Logic:**
The "Star" or "Nakshatra" is determined by the Moon's longitude.
*   The sky is divided into 27 sectors (Nakshatras) of 13°20' each.
*   Formula: `Nakshatra Index = floor(Moon_Longitude / 13.3333)`
*   We will use the **Skyfield** Python library (modern successor to Ephem) to get the Moon's position. Skyfield is pure-Python and easier to install in environments without C compilers.

## 2. Backend Implementation Steps

### Step 2.2: Create Calculation Module (`modules/panchang.py`)
Create a utility function `get_nakshatra(date_obj)`:
1.  Initialize a `skyfield.api.Loader` pointing to a local `data` directory.
2.  Load the `de421.bsp` ephemeris (standard, high-precision).
3.  Calculate the Moon's ecliptic longitude at 6:00 AM IST (Sunrise rule).
4.  Apply **Lahiri Ayanamsa** correction to convert Tropical longitude to Nirayana (Sidereal) longitude.5.  Divide by `13.3333` degrees (360 / 27).
6.  Map the integer result (0-26) to the Malayalam Star Name (Aswathi, Bharani, etc.).

### Step 2.3: Create API Endpoint (`routes/utility.py`)
Create a new route:
*   **URL**: `/utility/get-star`
*   **Method**: `GET`
*   **Params**: `date` (YYYY-MM-DD)
*   **Response**:
    ```json
    {
      "status": "success",
      "date": "2026-01-22",
      "nakshatra_eng": "Uthrattathi",
      "nakshatra_mal": "ഉത്രട്ടാതി"
    }
    ```

### Step 2.4: Create Inverse API (`/utility/get-next-star-dates`)
Create functionality to find the next 3 occurrences of a given star.
*   **Logic**: Iterate forward from today (up to 90 days). Calculate star for each day. If matches requested star, add to list.
*   **URL**: `/utility/get-next-star-dates`
*   **Params**: `star_name` (English), `start_date` (optional, default Today)
*   **Response**: `["2026-02-15", "2026-03-14"]`

## 3. Frontend Integration (Billing Page)

### Step 3.1: UI Update (`templates/cashier/billing.html`)
*   Next to the **"Vazhipadu Date"** input field, add a small info badge or text area: e.g., `<span id="dayStarDisplay" class="badge"></span>`.
*   Add a subtle "Auto-fill" button or make the badge clickable.

### Step 3.2: Javascript Logic
*   Add an event listener to the Date Input (`change` event).
*   On change, call the `/utility/get-star` API.
*   Update the `dayStarDisplay` text with the returned Star.
*   If the user hasn't manually selected a star yet, optionally auto-select the suggested star in the "Star" dropdown.

## 4. Dashboard Integration
*   In the Admin/Cashier Dashboard header, display **"Today's Star: [Star Name]"** for quick reference.

## 5. Execution Plan
1.  **Install Library**: `pip install skyfield`
2.  **Code Backend**: Implement `modules/panchang.py` and the API route.
3.  **Code Frontend**: Update `billing.html` to fetch and display the star.
4.  **Verify**: Compare calculated stars with a standard printed Malayalam calendar (Kalavara/Manorama) for accuracy adjustments. We use **Sunrise Rule** and **Lahiri Ayanamsa**.

---
**Permission to Proceed:**
Shall I begin by creating the `modules/panchang.py` module and installing the necessary library?
