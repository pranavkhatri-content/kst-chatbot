"""
KST knowledge base split into discrete chunks for RAG ingestion.

Each chunk has:
  - id:       unique identifier
  - topic:    human-readable label (also embedded)
  - queries:  anticipated user phrasings (embedded alongside topic+content
              to pull the vector closer to real user language)
  - doc_url:  canonical documentation link
  - content:  the knowledge the LLM reads at answer time
"""

CHUNKS = [
    # ── General / Conceptual ───────────────────────────────────────────────────
    {
        "id": "kst_overview",
        "topic": "What is KST / Overview",
        "doc_url": "https://docs.kelkoogroup.com/for-advertisers/kelkoo-sales-tracking",
        "queries": [
            "what is KST",
            "what is Kelkoo Sales Tracking",
            "how does KST work",
            "what are the lead tag and conversion tag",
            "what do I need to install for tracking",
            "KST overview",
            "explain Kelkoo Sales Tracking to me",
            "what does KST do",
        ],
        "content": """
What is KST?
Kelkoo Sales Tracking (KST) is a first-party cookie-based tracking solution that tracks sales on a merchant's website, associates them with users, and sends the data to Kelkoo servers to measure campaign performance.

The system requires two components installed on your website:
1. Lead Tag — a small script loaded on every page of the website. It creates a first-party cookie when a user first visits, identifying them as a Kelkoo click.
2. Conversion Tag — placed on the order confirmation page only. It retrieves data from the cookie and registers the sale with Kelkoo.

Both must be present for tracking to work. Missing either one means sales will not be recorded.

KST also functions as a Master Tag, similar to Google Tag Manager — it can host other tracking tags and trigger Google Global Site Tag to optimise traffic sourcing.
        """.strip()
    },
    {
        "id": "attribution_model",
        "topic": "Attribution model / conversion window",
        "doc_url": "https://docs.kelkoogroup.com/for-advertisers/kelkoo-sales-tracking/understanding-kelkoo-sales-tracking",
        "queries": [
            "how does KST attribution work",
            "what is the conversion window",
            "how long does the cookie last",
            "last click attribution",
            "why do my numbers differ from Google Analytics",
            "do I get credit if a customer converts through another channel later",
            "will I still get the sale if someone clicks elsewhere before buying",
            "who gets credit for the sale when multiple channels are involved",
        ],
        "content": """
Attribution Model:
KST uses a Kelkoo Channel Last Click attribution model with a 30-day conversion window.
- A sale is attributed to Kelkoo if the user clicked through Kelkoo at any point within 30 days before purchasing.
- This applies even if the user returned via another channel (e.g. Google, email) before converting.
- Attribution discrepancies may occur with other analytics platforms that use different last-click models.
        """.strip()
    },
    {
        "id": "gdpr_privacy",
        "topic": "GDPR / Privacy / Cookies",
        "doc_url": "https://docs.kelkoogroup.com/for-advertisers/kelkoo-sales-tracking/gdpr-notice-for-kelkoo-sales-tracking",
        "queries": [
            "is KST GDPR compliant",
            "what cookies does KST set",
            "do I need consent for KST",
            "KST privacy policy",
            "what data does KST collect",
            "cookie consent requirements",
            "what personal data does the tracking pixel collect",
            "where is my customer data stored",
            "what information does the KST pixel gather about visitors",
        ],
        "content": """
Privacy & GDPR:
KST sets three first-party cookies on the merchant's own domain:
- kelkooId: Measures Kelkoo ad campaign performance. Duration: 12 months.
- kk_gclid: Tracks Kelkoo Group campaign performance. Duration: 12 months.
- kk_leadtag: Determines tracking tool version deployed. Duration: 12 months.

GDPR Requirements:
- The Lead Tag requires user consent (marketing/analytics category) before firing.
- The Conversion Tag relies on legitimate interest — no explicit consent required.
- Merchants must configure their Consent Management Platform (CMP) accordingly.
- Data is stored in The Netherlands.
- Kelkoo Group is an independent data controller under GDPR.
- Data collected: user IDs, timestamps, URLs, IP addresses, location, user agents, and transaction details.
- DPO contact: dpo@kelkoogroup.com
        """.strip()
    },
    {
        "id": "merchant_id",
        "topic": "How to find Merchant ID and Country Code",
        "doc_url": "https://docs.kelkoogroup.com/for-advertisers/kelkoo-sales-tracking/installation-methods/how-to-get-your-merchantid-and-associated-country-code",
        "queries": [
            "where is my merchant ID",
            "how do I find my merchant ID",
            "where do I get my country code",
            "what merchant ID do I use",
            "campaign ID location",
        ],
        "content": """
How to Find Your Merchant ID and Country Code:
1. Log into Kelkoo Merchant Centre at merchant.kelkoogroup.com
2. Click the dropdown at the top left of the interface
3. Your Merchant ID and Country Code appear there — e.g. 100523248 | fr

Each campaign has its own Merchant ID + country code pair. If you run campaigns in multiple countries, you will have multiple Merchant IDs.
        """.strip()
    },
    {
        "id": "country_codes",
        "topic": "Country codes list",
        "doc_url": "https://docs.kelkoogroup.com/for-advertisers/kelkoo-sales-tracking/installation-methods/list-of-country-codes-at-kelkoo-group",
        "queries": [
            "list of country codes",
            "what country code for France",
            "what country code for Germany",
            "what country code for UK",
            "supported countries",
        ],
        "content": """
Country Codes (2-letter lowercase):
ae=United Arab Emirates, au=Australia, at=Austria, be=Belgium, br=Brazil, ca=Canada,
ch=Switzerland, cz=Czech Republic, de=Germany, dk=Denmark, gr=Greece, es=Spain,
fi=Finland, fr=France, hk=Hong Kong, ie=Ireland, in=India, id=Indonesia, it=Italy,
jp=Japan, kr=South Korea, my=Malaysia, mx=Mexico, nb=Flemish Belgium, nl=Netherlands,
no=Norway, nz=New Zealand, ph=Philippines, pl=Poland, pt=Portugal, ru=Russia,
se=Sweden, sg=Singapore, tr=Turkey, uk=United Kingdom, us=United States, vn=Vietnam, za=South Africa.
        """.strip()
    },

    # ── Pre-installation ───────────────────────────────────────────────────────
    {
        "id": "install_pre_steps",
        "topic": "Before any installation / remove legacy tags",
        "doc_url": "https://docs.kelkoogroup.com/for-advertisers/kelkoo-sales-tracking/installation-methods",
        "queries": [
            "what to do before installing KST",
            "remove old Kelkoo tracking",
            "legacy Kelkoo tags",
            "duplicate tracking tags",
        ],
        "content": """
Before Any Installation:
Always remove previous Kelkoo tracking first:
- Search your codebase for leadtag.js and _kkstrack
- Delete any matches found
- Uninstall any legacy Kelkoo plugins from your platform
        """.strip()
    },

    # ── GTM (split into 3 focused chunks) ──────────────────────────────────────
    {
        "id": "install_gtm_overview",
        "topic": "GTM installation overview",
        "doc_url": "https://docs.kelkoogroup.com/for-advertisers/kelkoo-sales-tracking/installation-methods/installation-via-google-tag-manager-gtm-with-enhanced-ecommerce",
        "queries": [
            "how to install KST with GTM",
            "Google Tag Manager setup for KST",
            "GTM installation steps overview",
            "can I use GTM for Kelkoo tracking",
            "how do I set up sales tracking with Google Tag Manager",
        ],
        "content": """
GTM Installation (Google Tag Manager) — Recommended Method:
GTM is the preferred method if you use GTM with custom triggers. Requires a good understanding of GTM. Supports multiple campaigns.

This method involves 5 steps:
1. Identify your Data Layer variables using GTM Preview mode and Tag Assistant
2. Create GTM Data Layer Variables for Order ID and Order Value
3. Create a Custom Event Trigger matching your purchase event
4. Install the Kelkoo Conversion Tag from the GTM template gallery
5. Install the Kelkoo Lead Tag as a Custom HTML tag on All Pages

After completing all steps, publish the GTM container.
        """.strip()
    },
    {
        "id": "install_gtm_datalayer",
        "topic": "GTM data layer variables and trigger setup",
        "doc_url": "https://docs.kelkoogroup.com/for-advertisers/kelkoo-sales-tracking/installation-methods/installation-via-google-tag-manager-gtm-with-enhanced-ecommerce",
        "queries": [
            "GTM data layer setup for KST",
            "how to find my data layer variables",
            "GTM preview mode purchase event",
            "create GTM trigger for KST",
            "order ID and order value variables in GTM",
        ],
        "content": """
GTM Steps 1-3: Data Layer Variables and Trigger Setup

Step 1 — Identify your Data Layer variables:
1. Enable GTM Preview mode from your GTM dashboard
2. Open Tag Assistant and enter your website URL — confirm "Connected" status
3. Complete a test transaction on your site
4. In Tag Assistant, find the purchase/sale event in the left panel
5. Click the dataLayer tab and note: the event name (e.g. purchase), the order ID path, the order value path

Step 2 — Create GTM Data Layer Variables:
1. In GTM go to Variables → New → Data Layer Variable
2. Create one variable for Order ID and one for Order Value
3. Save both

Step 3 — Create a Custom Event Trigger:
1. Go to Triggers → New → Custom Event
2. Set the event name to match Step 1 (e.g. purchase)
3. Save
        """.strip()
    },
    {
        "id": "install_gtm_tags",
        "topic": "GTM conversion tag and lead tag installation",
        "doc_url": "https://docs.kelkoogroup.com/for-advertisers/kelkoo-sales-tracking/installation-methods/installation-via-google-tag-manager-gtm-with-enhanced-ecommerce",
        "queries": [
            "install Kelkoo conversion tag in GTM",
            "install Kelkoo lead tag in GTM",
            "GTM tag template for Kelkoo",
            "how to add KST tags in Google Tag Manager",
            "publish GTM container for KST",
        ],
        "content": """
GTM Steps 4-5: Installing the Kelkoo Tags

Step 4 — Install the Kelkoo Conversion Tag:
1. Go to Tags → Templates → Search Gallery
2. Search for "Kelkoo Group Sales Tracking Tag" and add it to workspace
3. Create a new tag using this template
4. Configure: Country Code, Merchant ID, and your GTM variables
5. Assign the trigger from Step 3 → Save

Step 5 — Install the Kelkoo Lead Tag:
1. Create a new Custom HTML tag
2. Paste: <script async="true" type="text/javascript" src="https://s.kk-resources.com/leadtag.js"></script>
3. Set trigger to All Pages
4. Save and Publish the container
        """.strip()
    },

    # ── Manual ─────────────────────────────────────────────────────────────────
    {
        "id": "install_manual",
        "topic": "Manual installation",
        "doc_url": "https://docs.kelkoogroup.com/for-advertisers/kelkoo-sales-tracking/installation-methods/manual-installation-for-kelkoo-sales-tracking",
        "queries": [
            "manual KST installation",
            "install KST without a plugin",
            "add KST tracking code to my website",
            "KST code snippet for any platform",
            "how to add the lead tag and conversion tag manually",
            "how do I set up sales tracking without a plugin",
            "my website isn't built on Shopify WooCommerce or any known platform",
            "I have a custom-built website, not on a standard platform",
            "can I hard-code the tracking myself with no platform or plugin",
        ],
        "content": """
Manual Installation (any platform):
Works on any platform. Requires developer skills. Supports multiple campaigns.

Step 1 — Lead Tag (all pages):
Add to the end of the <head> section on every page:
<script async="true" type="text/javascript" src="https://s.kk-resources.com/leadtag.js"></script>

Step 2 — Conversion Tag (order confirmation page only):
Add just before </body> on the order confirmation page:
<script type="text/javascript">
_kkstrack = {
  merchantInfo: [{ country: 'COUNTRY_CODE', merchantId: 'MERCHANTID_VALUE' }],
  orderValue: 'ORDER_VALUE',
  orderId: 'ORDER_ID',
  basket: [{ productname: 'product name', productid: 'product-id', quantity: '1', price: '4.20' }]
};
(function() {
  var s = document.createElement('script');
  s.type = 'text/javascript'; s.async = true;
  s.src = 'https://s.kk-resources.com/ks.js';
  var x = document.getElementsByTagName('script')[0];
  x.parentNode.insertBefore(s, x);
})();
</script>

Parameters: country (2-letter lowercase), merchantId (from Merchant Centre), orderValue (decimal, no currency symbols), orderId (unique string), basket array with productname, productid, quantity, price.

Multiple campaigns: merchantInfo: [{ country: 'fr', merchantId: '12941513' }, { country: 'uk', merchantId: '56789' }]
        """.strip()
    },

    # ── Shopify ────────────────────────────────────────────────────────────────
    {
        "id": "install_shopify",
        "topic": "Shopify / Shopify Plus installation",
        "doc_url": "https://docs.kelkoogroup.com/for-advertisers/kelkoo-sales-tracking/installation-methods/installation-guides-for-ecommerce-platforms/shopify-shopify-plus",
        "queries": [
            "install KST on Shopify",
            "Shopify Plus KST setup",
            "Shopify custom pixel for Kelkoo",
            "Shopify customer events tracking",
            "Kelkoo tracking on Shopify",
            "how do I set up sales tracking on Shopify",
            "I'm on Shopify how do I set up tracking",
        ],
        "content": """
Shopify / Shopify Plus Installation:
Uses Shopify's Customer Events (Custom Pixels) — the current Shopify tracking approach.

Step 1 — Create the Lead Tag pixel:
1. Shopify Admin → Settings → Customer Events
2. Click Add Custom Pixel → Name it: Kelkoo Leadtag
3. Paste this code:
(function() {
  var leadTag = document.createElement('script');
  leadTag.src = 'https://s.kk-resources.com/leadtag.js';
  leadTag.async = true;
  document.head.appendChild(leadTag);
})();
4. Permission: Required Marketing/Analytics
5. Data Sale: Data collected does not qualify as data sale
6. Click Connect

Step 2 — Create the Conversion Tag pixel:
1. Settings → Customer Events → Add Custom Pixel → Name: Kelkoo Conversion
2. Paste this code (replace country code and merchant ID):
analytics.subscribe("checkout_completed", event => {
  var basketFull = [];
  for (i = 0; i < event.data.checkout.lineItems.length; i++) {
    var basketContent = {
      productname: event.data.checkout.lineItems[i].title,
      productid: event.data.checkout.lineItems[i].id,
      quantity: event.data.checkout.lineItems[i].quantity,
      price: event.data.checkout.lineItems[i].variant.price
    };
    basketFull.push(basketContent);
  }
  _kkstrack = {
    merchantInfo: [{ country: 'ADD YOUR COUNTRY CODE HERE', merchantId: 'ADD YOUR MERCHANT ID HERE' }],
    orderValue: event.data.checkout.totalPrice.amount,
    orderId: event.data.checkout.order.id,
    basket: basketFull
  };
  var s = document.createElement('script');
  s.type = 'text/javascript'; s.async = true;
  s.src = 'https://s.kk-resources.com/ks.js';
  document.getElementsByTagName('script')[0].parentNode.insertBefore(s, arguments[0].parentNode);
});
3. Permission: Not Required
4. Data Sale: Data collected does not qualify as data sale
5. Click Connect
        """.strip()
    },

    # ── WooCommerce ────────────────────────────────────────────────────────────
    {
        "id": "install_woocommerce",
        "topic": "WooCommerce installation",
        "doc_url": "https://docs.kelkoogroup.com/for-advertisers/kelkoo-sales-tracking/installation-methods/installation-guides-for-ecommerce-platforms/woocommerce",
        "queries": [
            "install KST on WooCommerce",
            "WooCommerce Kelkoo plugin",
            "WordPress KST tracking setup",
            "Kelkoo WooCommerce plugin settings",
            "how do I set up sales tracking on WooCommerce",
            "I'm on WooCommerce how do I set up tracking",
        ],
        "content": """
WooCommerce (WordPress Plugin) Installation:
WooCommerce installation uses an official Kelkoo plugin — no code editing needed.

Install via WordPress Dashboard:
1. WordPress Admin → Plugins → Add New
2. Search: Kelkoo Group sales tracking
3. Click Install Now → Activate

Or install manually:
1. Download the plugin from WordPress.org
2. Extract the zip to /wp-content/plugins/
3. Go to Plugins → Activate

Configure:
1. Open the plugin settings
2. Enter your Merchant ID in the Merchant Identifier field
3. Enter your Country Code (2-letter lowercase) in the Country field
4. Save
        """.strip()
    },

    # ── PrestaShop (split by version) ──────────────────────────────────────────
    {
        "id": "install_prestashop_8_17",
        "topic": "PrestaShop 8 and 1.7 installation",
        "doc_url": "https://docs.kelkoogroup.com/for-advertisers/kelkoo-sales-tracking/installation-methods/installation-guides-for-ecommerce-platforms/prestashop-8",
        "queries": [
            "install KST on PrestaShop 8",
            "install KST on PrestaShop 1.7",
            "PrestaShop KST tracking setup",
            "Kelkoo tracking for PrestaShop",
            "PrestaShop head.tpl lead tag",
            "how do I set up sales tracking on PrestaShop",
            "I'm on PrestaShop 8 how do I set up tracking",
        ],
        "content": """
PrestaShop Installation (versions 8 and 1.7):

Before starting: Enable template recompilation: Admin → Advanced Parameters → Performance → "Recompile templates if files have been updated". Back up all files.

Step 1 — Lead Tag: Open themes/[your-theme]/templates/_partials/head.tpl and add:
<script async="true" type="text/javascript" src="https://s.kk-resources.com/leadtag.js"></script>
Clear cache: Admin → Advanced Parameters → Performance → Clear Cache.

Step 2 — Modify OrderConfirmationController.php to capture product data into products_json, sales, and orderid template variables.

Step 3 — Conversion Tag: Add to themes/[your-theme]/templates/checkout/_partials/order-confirmation-table.tpl:
<script type="text/javascript">
  _kkstrack = {
    merchantInfo: [{ country: "COUNTRY", merchantId: "MERCHANTID_VALUE" }],
    orderValue: '{$sales}', orderId: '{$orderid}', basket: {$products_json nofilter}
  };
  (function() { var s = document.createElement('script'); s.type='text/javascript'; s.async=true; s.src='https://s.kk-resources.com/ks.js'; var x=document.getElementsByTagName('script')[0]; x.parentNode.insertBefore(s,x); })();
</script>
Note: reinstallation required after any PrestaShop or theme updates.
        """.strip()
    },
    {
        "id": "install_prestashop_16",
        "topic": "PrestaShop 1.6 installation",
        "doc_url": "https://docs.kelkoogroup.com/for-advertisers/kelkoo-sales-tracking/installation-methods/installation-guides-for-ecommerce-platforms/prestashop-8",
        "queries": [
            "install KST on PrestaShop 1.6",
            "PrestaShop 1.6 Kelkoo tracking",
            "PrestaShop 1.6 header.tpl lead tag",
            "PrestaShop 1.6 PayPal module KST",
            "how do I set up sales tracking on PrestaShop 1.6",
        ],
        "content": """
PrestaShop 1.6 Installation:

Lead Tag: Open themes/[your-theme]/header.tpl and append:
<script async="true" type="text/javascript" src="https://s.kk-resources.com/leadtag.js"></script>

Conversion Tag: Add to themes/[your-theme]/order-confirmation.tpl with literal tags around merchantInfo.
PayPal module: If PayPal enabled, apply same changes to /modules/paypal/controllers/front/submit.php and its template.
        """.strip()
    },

    # ── Magento (split by version) ─────────────────────────────────────────────
    {
        "id": "install_magento2",
        "topic": "Magento 2 installation",
        "doc_url": "https://docs.kelkoogroup.com/for-advertisers/kelkoo-sales-tracking/installation-methods/installation-guides-for-ecommerce-platforms/magento",
        "queries": [
            "install KST on Magento 2",
            "Magento 2 Kelkoo tracking module",
            "Magento 2 lead tag XML layout",
            "Kelkoo module for Magento 2",
            "how do I set up sales tracking on Magento 2",
            "I'm on Magento 2 how do I set up tracking",
            "I use Magento 2 for my store how do I track sales",
        ],
        "content": """
Magento 2 Installation (up to version 2.3):

Lead Tag: Add to YourTheme/Magento_Theme/layout/default_head_blocks.xml:
<script src="https://s.kk-resources.com/leadtag.js" src_type="url"/>

Conversion Tag:
1. Create /app/code/ directory if it doesn't exist
2. Download the Kelkoo module from the GitHub link in the official documentation
3. Extract to /app/code/
4. Update country and merchantId in the success template file
5. Enable the module via CLI
        """.strip()
    },
    {
        "id": "install_magento1",
        "topic": "Magento 1 installation",
        "doc_url": "https://docs.kelkoogroup.com/for-advertisers/kelkoo-sales-tracking/installation-methods/installation-guides-for-ecommerce-platforms/magento",
        "queries": [
            "install KST on Magento 1",
            "Magento 1 Kelkoo tracking",
            "Magento 1 checkout success.phtml",
            "Magento 1 XML layout lead tag",
            "how do I set up sales tracking on Magento 1",
            "I'm on Magento 1 how do I set up tracking",
        ],
        "content": """
Magento 1 Installation:

Lead Tag: Add to your XML layout file inside <reference name="head"> block using core/text block type.
Conversion Tag: Edit web/app/design/frontend/custom/default/template/checkout/success.phtml — use PHP to retrieve Order object and fire the _kkstrack conversion script.
        """.strip()
    },

    # ── LightSpeed ─────────────────────────────────────────────────────────────
    {
        "id": "install_lightspeed",
        "topic": "LightSpeed C-Series installation",
        "doc_url": "https://docs.kelkoogroup.com/for-advertisers/kelkoo-sales-tracking/installation-methods/installation-guides-for-ecommerce-platforms/lightspeed-c-series",
        "queries": [
            "install KST on LightSpeed",
            "LightSpeed C-Series Kelkoo tracking",
            "LightSpeed web extras tracking code",
            "how do I set up sales tracking on LightSpeed",
            "I'm on LightSpeed how do I set up tracking",
        ],
        "content": """
LightSpeed C-Series Installation:
Step 1: Log into LightSpeed and go to Web Extras from the left sidebar.
Step 2 — Lead Tag: In the Custom JavaScript section, add:
<script async="true" type="text/javascript" src="https://s.kk-resources.com/leadtag.js"></script>
Step 3 — Conversion Tag: In the Tracking Code section, add (replace COUNTRY_CODE and MERCHANT_ID):
_kkstrack = {
  merchantInfo: [{ country: 'COUNTRY_CODE', merchantId: 'MERCHANT_ID' }],
  orderValue: '{{ order.information.price_incl }}',
  orderId: '{{ order.information.number }}',
  basket: [{% for product in order.products %}{...}{% endfor %}]
};
Step 4: Save and run a test purchase to verify tracking.
        """.strip()
    },

    # ── Unas ───────────────────────────────────────────────────────────────────
    {
        "id": "install_unas",
        "topic": "Unas Ecommerce installation",
        "doc_url": "https://docs.kelkoogroup.com/for-advertisers/kelkoo-sales-tracking/installation-methods/installation-guides-for-ecommerce-platforms/unas-ecommerce",
        "queries": [
            "install KST on Unas",
            "Unas ecommerce Kelkoo tracking",
            "Unas marketing external systems",
            "how do I set up sales tracking on Unas",
            "I'm on Unas how do I set up tracking",
        ],
        "content": """
Unas Ecommerce Installation:
Step 1: In your Unas dashboard, go to Marketing → External marketing systems
Step 2: Click Add next to the Kelkoo Group logo
Step 3: Enter your merchantId in the activation field
Step 4: Verify the country setting matches the languages configured under Settings → Texts, Languages → Setting languages
Step 5: Save
Multiple campaigns: Go to Settings → Texts, Languages → Setting languages, add the required language/country combinations, and configure each corresponding merchantId.
        """.strip()
    },

    # ── Server-to-Server ───────────────────────────────────────────────────────
    {
        "id": "install_server_to_server",
        "topic": "Server-to-server implementation (advanced)",
        "doc_url": "https://docs.kelkoogroup.com/for-advertisers/kelkoo-sales-tracking/installation-methods/advanced-setup/server-to-server-implementation",
        "queries": [
            "server-to-server KST implementation",
            "backend KST tracking without JavaScript",
            "KST API integration",
            "server side Kelkoo tracking",
            "advanced KST setup",
            "how do I set up sales tracking server to server",
        ],
        "content": """
Server-to-Server Implementation (Advanced):
A backend implementation. Requires an in-house development team (~5 days minimum). Does not rely on browser scripts.

How it works:
1. When a user lands on your site, capture and store kelkooId, gclid, and msclkid URL parameters in your database, linked to their session or basket.
2. On order confirmation, retrieve the stored IDs and send an HTTP GET request to: https://s.kelkoogroup.net/st

Required parameters: country (2-letter code), orderId, comId (Merchant ID), orderValue, productsInfos (URL-encoded Base64 JSON array), saleId (random 0-1), kelkooId (optional), gclid (optional), msclkid (optional), returningUser (optional).
Code examples available for PHP 5.5+, Java 8, Python 3.x, and Node.js 20.x.
Consent must be managed directly by the merchant separately from traditional cookie mechanisms.
        """.strip()
    },

    # ── Testing ────────────────────────────────────────────────────────────────
    {
        "id": "testing",
        "topic": "Testing your KST setup",
        "doc_url": "https://docs.kelkoogroup.com/for-advertisers/kelkoo-sales-tracking/installation-methods/test-your-kelkoo-sales-tracking-setup",
        "queries": [
            "how to test KST",
            "test my KST pixel",
            "verify KST installation",
            "check if KST is working",
            "KST tester wizard",
            "no sales showing in Merchant Centre",
        ],
        "content": """
Testing Your KST Setup:
1. Log into Kelkoo Merchant Centre at merchant.kelkoogroup.com
2. Select your campaign from the top-left dropdown
3. Click "Kelkoo Sales Tracking Installer" in the left menu
4. Use the Tester wizard (3 guided steps)
5. Check the Status section for errors or warnings
6. Check Last Call Registered to see recent pixel calls and transmitted data
7. The following day, check Statistics in Merchant Centre to confirm sales appear with correct order values

Primary debugging tool: https://merchant.kelkoogroup.com/app/campaign/sales-tracking
        """.strip()
    },

    # ── Troubleshooting ────────────────────────────────────────────────────────
    {
        "id": "troubleshooting_general",
        "topic": "Troubleshooting general / no conversions showing",
        "doc_url": "https://docs.kelkoogroup.com/for-advertisers/kelkoo-sales-tracking/troubleshooting",
        "queries": [
            "KST not working",
            "no conversions showing",
            "sales not tracking",
            "pixel not firing",
            "troubleshoot KST",
            "KST debugging",
            "zero sales in dashboard",
            "my tracking is completely broken and I'm losing money",
            "the pixel never fires and no sales are being recorded at all",
            "everything is broken, nothing is tracking, fix this",
        ],
        "content": """
General Troubleshooting Checklist (All Platforms):
- Both Lead Tag (all pages) AND Conversion Tag (confirmation page only) are installed
- No duplicate/legacy Kelkoo tags (leadtag.js / _kkstrack) in the code
- Lead Tag fires with user consent (required by GDPR)
- Merchant ID and Country Code are correct
- orderValue is a plain decimal number — no currency symbols (£, €, $)
- orderId is unique per transaction

If issues remain: use the KST Debugging Tool at https://merchant.kelkoogroup.com/app/campaign/sales-tracking
Or contact Kelkoo Support via the contact form in Merchant Centre with subject: "Kelkoo Sales Tracking troubleshooting"
        """.strip()
    },
    {
        "id": "troubleshooting_gtm",
        "topic": "GTM troubleshooting",
        "doc_url": "https://docs.kelkoogroup.com/for-advertisers/kelkoo-sales-tracking/troubleshooting/troubleshooting-gtm-integration",
        "queries": [
            "GTM KST not working",
            "GTM tag not firing",
            "orderId undefined in GTM",
            "orderValue undefined in GTM",
            "data layer not read correctly",
            "GTM container not published",
        ],
        "content": """
GTM-Specific Troubleshooting:
- Integration not working at all: Ensure you have published the container
- orderId / orderValue undefined: Re-install using the current Kelkoo GTM template; verify variable mappings in debug mode
- Datalayer not read correctly: The datalayer must appear above the GTM snippet in your source code
- Tag fires too early: Change trigger type to "Page View - DOM ready" instead of "All Pages Page View"
- Variable syntax errors: Use double brackets {{variableName}} and standard ASCII quotes, not curly quotes
- Tag priority issue: In tag Advanced Settings, set priority to 3 for the custom HTML lead tag
        """.strip()
    },
    {
        "id": "troubleshooting_shopify",
        "topic": "Shopify troubleshooting",
        "doc_url": "https://docs.kelkoogroup.com/for-advertisers/kelkoo-sales-tracking/troubleshooting/troubleshooting-shopify-integration",
        "queries": [
            "Shopify KST not working",
            "Shopify pixel not firing",
            "Shopify revenue formatting error",
            "Shopify tracking not on all devices",
        ],
        "content": """
Shopify-Specific Troubleshooting:
- Tag not firing on all devices: Ensure the pixel is not placed inside a device-specific section — it must be in a universal location
- Revenue over 4 digits has formatting errors: Adapt the orderValue code based on your Shopify money format:
  * {{ amount }} → use remove: ','
  * {{ amount_with_comma_separator }} → use remove: '.' | replace: ',', '.'
  * {{ amount_with_apostrophe_separator }} → use remove: "'"
        """.strip()
    },
    {
        "id": "troubleshooting_prestashop",
        "topic": "PrestaShop troubleshooting",
        "doc_url": "https://docs.kelkoogroup.com/for-advertisers/kelkoo-sales-tracking/troubleshooting/troubleshooting-prestashop-integration",
        "queries": [
            "PrestaShop KST not working",
            "PrestaShop variables not replaced",
            "PrestaShop literal tags issue",
            "PrestaShop cache not clearing",
        ],
        "content": """
PrestaShop-Specific Troubleshooting:
- Variables not replaced in source: Check there are no {literal} tags wrapping the <script> tag containing _kkstrack
- Wrong file edited: Confirm you edited the correct template file for your PrestaShop version
- Changes not taking effect: Clear cache: Admin → Advanced → Performance → Refresh cache
        """.strip()
    },

    # ── Performance ────────────────────────────────────────────────────────────
    {
        "id": "performance",
        "topic": "Performance and SPA notes",
        "doc_url": "https://docs.kelkoogroup.com/for-advertisers/kelkoo-sales-tracking",
        "queries": [
            "does KST slow down my site",
            "KST performance impact",
            "KST on single page application",
            "KST file size",
            "how fast is KST",
        ],
        "content": """
KST Performance:
KST is lightweight and fully asynchronous:
- Lead tag: 100 ms download time, 2.9 kB compressed
- Conversion tag: 22 ms download time, 3.9 kB compressed
- Webservice call: ~180 ms

For Single-Page Applications (SPAs): the lead tag only needs to load once per user, not on each virtual page load.
        """.strip()
    },
]
