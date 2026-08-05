# HeyDay Realty - Manual Testing Use Case

## UC-01: Property listing to customer inquiry

**Purpose:** Verify the end-to-end journey in which an agent lists a property, an administrator reviews it, and a customer finds and submits an inquiry for it.

**Priority:** High  
**Roles:** Agent, Administrator, Customer  
**Test data:** Use unique values (for example, prefix the property title and email with `QA-<date>-`) so they can be identified and removed after testing.

### Preconditions

- The application is running and reachable by the tester.
- A verified agent account, an administrator account, and a customer account are available.
- The agent has completed any required profile/KYC verification.
- The test property does not already exist.

### Test steps and expected results

| Step | Tester / role | Action | Expected result |
| --- | --- | --- | --- |
| 1 | Agent | Sign in at `/auth/login/`. | Login succeeds and the user is directed to the agent dashboard (`/agent/dashboard/`) or can reach it from the navigation. |
| 2 | Agent | Open **Properties** and choose **Add Property**. Select a property type. | The property form for the selected type is displayed. |
| 3 | Agent | Enter all mandatory property information, including a unique title, price, location, description, contact details, and at least one valid image if required. Submit the form. | The property is created. It appears in the agent's property list and is marked with the appropriate pending/review status. Validation messages are shown for any missing required value. |
| 4 | Administrator | Sign in and open **Property Review** at `/admin-dashboard/property-review/`. | The newly submitted property is visible in the review queue. |
| 5 | Administrator | Open the property detail and verify its listing information and image. Approve the property. | The status changes to approved. The property no longer appears as pending, and its review outcome is recorded. |
| 6 | Customer | Sign in at `/auth/login/`, then open `/buy/` or `/properties/`. Search or filter using the title/location entered in step 3. | The approved property is returned. Its title, price, location, and image match the agent’s submission. |
| 7 | Customer | Open the property detail. | The detail page loads and shows the approved property information. The customer can access the inquiry action. |
| 8 | Customer | Submit an inquiry from the property page, providing a valid message and contact information. | A success confirmation is shown. The same inquiry is not created twice if the submit button is clicked repeatedly. |
| 9 | Agent | Open **Leads** or **Communications** from the agent dashboard. | The customer inquiry is visible with the correct customer and property details. |
| 10 | Agent | Add a follow-up note or send a communication to the customer. | The follow-up/communication is saved and appears in the relevant lead or communication history. |

### Acceptance criteria

- An agent can create a valid listing without administrative access.
- An unapproved listing is not publicly discoverable.
- An administrator can approve the listing through the property-review workflow.
- An approved listing is discoverable by a customer and shows correct information.
- A customer inquiry is retained and visible to the agent for follow-up.
- Each role is prevented from performing actions reserved for another role.

### Negative and access-control checks

| ID | Action | Expected result |
| --- | --- | --- |
| UC-01-N01 | Submit the agent property form with a required field blank. | The property is not created; a clear validation message identifies the missing field. |
| UC-01-N02 | Before approval, search for the property while logged out or as a customer. | The pending property is not shown in public/customer search results. |
| UC-01-N03 | Open `/admin-dashboard/property-review/` while signed in as an agent or customer. | Access is denied or redirected to the unauthorized page; no review data is disclosed. |
| UC-01-N04 | Open `/agent/properties/` while signed in as a customer. | Access is denied or redirected; the customer cannot manage agent properties. |
| UC-01-N05 | Try to submit an inquiry without the required information. | The inquiry is not created and validation feedback is displayed. |

### Evidence to attach to the test result

- Screenshot of the agent's created listing and its initial status.
- Screenshot of the administrator approval result.
- Screenshot of the property as displayed in search/detail.
- Screenshot of the customer inquiry confirmation and the agent's received lead.
- Defect ID(s), if any expected result fails.

### Result record

| Executed by | Date | Build / environment | Result (Pass / Fail / Blocked) | Notes / defect ID |
| --- | --- | --- | --- | --- |
|  |  |  |  |  |
