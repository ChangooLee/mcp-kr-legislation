[한국어](README.md) | English

# MCP Korean Legislation Information Server

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)
![FastMCP](https://img.shields.io/badge/FastMCP-Latest-green.svg)
![GitHub Stars](https://img.shields.io/github/stars/ChangooLee/mcp-kr-legislation)
![GitHub Issues](https://img.shields.io/github/issues/ChangooLee/mcp-kr-legislation)

Model Context Protocol (MCP) server integrating Korean Ministry of Legislation OPEN APIs. **130+ comprehensive tools** provide complete access to all Korean legal information including laws, additional services, administrative rules, ordinances, precedents, committee decisions, treaties, forms, school regulations, legal terms, custom services, knowledge base, special administrative trials, and ministry interpretations.

**🔗 GitHub Repository**: https://github.com/ChangooLee/mcp-kr-legislation

---

## 🌟 Key Features

- **📚 Comprehensive Legal Information**: All legislation from current laws to precedents, treaties, and committee decisions
- **🔍 Powerful Search**: Detailed search by legislation name, content, and ministry
- **🌍 Multilingual Support**: Both Korean original and English translations
- **⚡ Real-time Updates**: Real-time data connection with Ministry of Legislation
- **🔗 Direct API Access**: Actual API URLs included in each response for direct verification
- **📊 Rich Information**: Detailed content including legislation articles, precedent summaries, committee decision rationales
- **🤖 AI-Friendly**: Perfect integration with AI tools like Claude Desktop

---

## Example Usage

Ask your AI assistant to:

### Basic Search Questions
- **📚 Legislation Search** - "Find the latest content of the Personal Information Protection Act"
- **🔍 Case Search** - "Search for recent cases related to personal information protection"
- **📖 Treaty Lookup** - "Find FTA treaties that Korea has concluded"
- **🏛️ Local Ordinances** - "Find Seoul's ordinances related to personal information protection"
- **📋 Administrative Rules** - "Show me Ministry of Employment and Labor rules for worker protection"

### Advanced Search Questions
- **🔬 Comprehensive Analysis** - "Systematically investigate the legal basis for financial companies collecting marital status information and create a comprehensive report"
- **⚖️ Case Analysis** - "Analyze trends in Personal Information Protection Act violation cases over the past 5 years"
- **🏛️ Committee Decisions** - "Find decisions by the Personal Information Protection Committee regarding marital status collection"
- **📊 Legal Comparison** - "Compare personal information collection regulations between the Personal Information Protection Act and Credit Information Act"

---

## 🛠️ Complete Tool List (By Category)

### 1. Legislation Tools (45 tools)
| Tool Name | Function | Test Question |
|-----------|----------|---------------|
| `search_law` | Current legislation search | "Search for Personal Information Protection Act" |
| `search_english_law` | English legislation search | "Find Personal Information Protection Act in English" |
| `search_effective_law` | Effective date legislation search | "What personal information related laws are scheduled to take effect recently?" |
| `search_law_nickname` | Legislation nickname search | "What is the official name for the nickname 'Privacy Act'?" |
| `search_deleted_law_data` | Deleted legislation data search | "Find repealed personal information related laws" |
| `search_law_articles` | Legislation articles search | "Show article-by-article content of Personal Information Protection Act" |
| `search_law_with_cache` | Cached legislation search | "Quickly search for Banking Act" |
| `get_law_summary` | Legislation summary retrieval | "Show summary of Personal Information Protection Act" |
| `get_english_law_detail` | English legislation details | "What are the detailed contents of English Personal Information Protection Act?" |
| `search_old_and_new_law` | Old vs new law comparison | "Show before and after comparison of Personal Information Protection Act amendments" |
| `search_three_way_comparison` | Three-way comparison | "Show 3-stage comparison of Personal Information Protection Act" |
| `search_deleted_history` | Deletion history inquiry | "What recently deleted legislation data is there?" |
| `search_one_view` | At-a-glance view | "Show summary information of Personal Information Protection Act" |
| `search_law_system_diagram` | Law system diagram | "Show law system diagram of Personal Information Protection Act" |
| `get_law_system_diagram_detail` | System diagram details | "Show detailed system diagram content" |
| `get_delegated_law` | Delegated law inquiry | "Show delegated laws of Personal Information Protection Act" |
| `search_custom_law` | Custom law search | "Show custom laws by classification code" |
| `search_custom_law_articles` | Custom law articles | "Find custom law articles" |
| `search_law_appendix` | Law appendix and forms search | "Show appendices and forms of Personal Information Protection Act" |

### 2. Administrative Rules/Local Ordinances Tools (8 tools)
| Tool Name | Function | Test Question |
|-----------|----------|---------------|
| `search_administrative_rule` | Administrative rules search | "Find administrative rules related to personal information protection" |
| `get_administrative_rule_detail` | Administrative rule details | "Show content of specific administrative rule" |
| `search_administrative_rule_comparison` | Administrative rule old vs new | "Compare before and after administrative rule amendments" |
| `get_administrative_rule_comparison_detail` | Comparison details | "Show detailed content of administrative rule comparison" |
| `search_local_ordinance` | Local ordinance search | "Find Seoul personal information protection ordinances" |
| `search_ordinance_appendix` | Local ordinance appendices | "Show ordinance appendices and forms" |
| `search_linked_ordinance` | Linked local ordinances | "What ordinances are linked to Personal Information Protection Act?" |
| `get_local_ordinance_detail` | Local ordinance details | "Show detailed content of specific local ordinance" |

### 3. Precedent Tools (8 tools)
| Tool Name | Function | Test Question |
|-----------|----------|---------------|
| `search_precedent` | Supreme Court precedent search | "Find personal information protection related precedents" |
| `search_constitutional_court` | Constitutional Court decisions | "What are Constitutional Court decisions on personal information protection?" |
| `search_legal_interpretation` | Legal interpretation cases | "Show legal interpretations on personal information collection" |
| `search_administrative_trial` | Administrative trial cases | "What are administrative trial cases on personal information protection?" |
| `get_precedent_detail` | Precedent details | "Show detailed content of specific precedent" |
| `get_constitutional_court_detail` | Constitutional Court details | "Show detailed content of specific Constitutional Court decision" |
| `get_legal_interpretation_detail` | Legal interpretation details | "Show detailed content of specific legal interpretation" |
| `get_administrative_trial_detail` | Administrative trial details | "Show detailed content of specific administrative trial case" |

### 4. Committee Decision Tools (24 tools)
| Tool Name | Function | Test Question |
|-----------|----------|---------------|
| `search_privacy_committee` | Personal Information Protection Committee decision search | "What are committee decisions on marital status collection?" |
| `search_financial_committee` | Financial Services Commission decision search | "What are financial committee decisions on personal information?" |
| `search_monopoly_committee` | Fair Trade Commission decision search | "What are fair trade committee decisions on personal information?" |
| `search_anticorruption_committee` | Anti-Corruption Committee decision search | "Find anti-corruption committee decisions" |
| `search_labor_committee` | Labor Relations Commission decision search | "What are labor committee decisions on personal information?" |
| `search_environment_committee` | Environmental Dispute Committee decision search | "Show environment committee decisions" |
| `search_securities_committee` | Securities and Futures Commission decision search | "What are securities committee decisions on personal information?" |
| `search_human_rights_committee` | National Human Rights Commission decision search | "What are human rights committee decisions on personal information?" |
| `search_broadcasting_committee` | Korea Communications Commission decision search | "Find broadcasting committee decisions" |
| `search_industrial_accident_committee` | Industrial Accident Compensation Committee decision search | "Show industrial accident committee decisions" |
| `search_land_tribunal` | Central Land Expropriation Committee decision search | "Find land expropriation committee decisions" |
| `search_employment_insurance_committee` | Employment Insurance Review Committee decision search | "Show employment insurance committee decisions" |
| 12 detail tools | Individual committee decision details | "Show detailed content of specific committee decision" |

### 5. Ministry Interpretation Tools (19 tools)
| Tool Name | Function | Test Question |
|-----------|----------|---------------|
| `search_moef_interpretation` | Ministry of Economy and Finance interpretation | "Show MOEF personal information related interpretations" |
| `search_molit_interpretation` | Ministry of Land, Infrastructure and Transport interpretation | "Find MOLIT legal interpretations" |
| `search_moel_interpretation` | Ministry of Employment and Labor interpretation | "What are MOEL personal information related interpretations?" |
| `search_mof_interpretation` | Ministry of Oceans and Fisheries interpretation | "Show MOF legal interpretations" |
| `search_mohw_interpretation` | Ministry of Health and Welfare interpretation | "What are MOHW personal information related interpretations?" |
| `search_moe_interpretation` | Ministry of Education interpretation | "Find MOE legal interpretations" |
| `search_korea_interpretation` | Government-wide interpretations | "Show government-wide legal interpretations" |
| `search_mssp_interpretation` | Ministry of Patriots and Veterans Affairs interpretation | "Find MSSP legal interpretations" |
| `search_mote_interpretation` | Ministry of Trade, Industry and Energy interpretation | "Show MOTE legal interpretations" |
| `search_maf_interpretation` | Ministry of Agriculture, Food and Rural Affairs interpretation | "Find MAF legal interpretations" |
| `search_moms_interpretation` | Ministry of National Defense interpretation | "Show MOMS legal interpretations" |
| `search_sme_interpretation` | Ministry of SMEs and Startups interpretation | "Find SME ministry legal interpretations" |
| `search_nfa_interpretation` | Korea Forest Service interpretation | "Show KFS legal interpretations" |
| `search_korail_interpretation` | Korea Railroad Corporation interpretation | "Find KORAIL legal interpretations" |
| `search_nts_interpretation` | National Tax Service interpretation | "Find NTS legal interpretations" |
| `search_kcs_interpretation` | Korea Customs Service interpretation | "Find KCS legal interpretations" |
| 3 detail tools | Individual ministry interpretation details | "Show detailed content of specific ministry interpretation" |

### 6. Specialized Tools (6 tools)
| Tool Name | Function | Test Question |
|-----------|----------|---------------|
| `search_treaty` | Treaty search | "Find international treaties related to personal information protection" |
| `search_university_regulation` | University regulation search | "Find university personal information protection regulations" |
| `search_public_corporation_regulation` | Public corporation regulation search | "Show corporation personal information regulations" |
| `search_public_institution_regulation` | Public institution regulation search | "Find public institution personal information regulations" |
| `search_tax_tribunal` | Tax Tribunal case search | "What are tax tribunal cases on personal information?" |
| `search_maritime_safety_tribunal` | Korea Maritime Safety Tribunal case search | "Find maritime safety tribunal cases" |

### 7. Knowledge Base/Consultation Tools (6 tools)
| Tool Name | Function | Test Question |
|-----------|----------|---------------|
| `search_knowledge_base` | Knowledge base search | "Find personal information protection knowledge base" |
| `search_faq` | Frequently asked questions search | "Show personal information protection related FAQ" |
| `search_qna` | Q&A search | "Find Q&A on personal information collection" |
| `search_counsel` | Consultation content search | "Show personal information protection consultation cases" |
| `search_precedent_counsel` | Precedent consultation search | "Find precedent-related consultation content" |
| `search_civil_petition` | Civil petition search | "Show personal information protection related petition cases" |

### 8. Legal Terms Tools (6 tools)
| Tool Name | Function | Test Question |
|-----------|----------|---------------|
| `search_legal_term` | Legal term search | "Show legal definition of personal information" |
| `search_legal_term_ai` | AI legal term search | "Search legal terms using AI" |
| `search_daily_term` | Daily term search | "Find legal terms using daily language" |
| `search_daily_legal_term_link` | Daily-legal term linkage | "Show connections between daily and legal terms" |
| `search_legal_daily_term_link` | Legal-daily term linkage | "Show connections between legal and daily terms" |
| `get_legal_term_detail` | Legal term details | "Show detailed definition of specific legal term" |

### 9. Custom/Miscellaneous Tools (9 tools)
| Tool Name | Function | Test Question |
|-----------|----------|---------------|
| `search_custom_ordinance` | Custom local ordinance search | "Show custom local ordinances" |
| `search_custom_ordinance_articles` | Custom ordinance articles search | "Find custom ordinance articles" |
| `search_custom_precedent` | Custom precedent search | "Show custom precedents" |
| `get_ordinance_detail` | Local ordinance details | "Show detailed content of specific local ordinance" |
| `get_treaty_detail` | Treaty details | "Show detailed content of specific treaty" |
| `get_ordinance_appendix_detail` | Local ordinance appendix details | "Show detailed content of local ordinance appendix" |
| `search_legal_ai` | AI-based comprehensive legal search | "Show AI-based personal information protection information" |
| `search_all_legal_documents` | Integrated legal document search | "Comprehensively search all legal documents related to personal information protection" |

**Complete access to all Korean legal information with 130+ comprehensive tools**

---

## Quick Start Guide

### 1. API Key Setup

Korean Ministry of Legislation API is **free** and requires only an email address:

1. No registration or application process required
2. Use your email address as the API key
3. Ready to use immediately

### 2. Installation

```bash
# Clone repository
git clone https://github.com/ChangooLee/mcp-kr-legislation.git
cd mcp-kr-legislation

# [IMPORTANT] Python 3.10+ required. See 'Python 3.10+ Installation Guide' below

# Create virtual environment
python3.10 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .
```

### 3. Environment Variables Setup

Create a `.env` file with the following configuration:

```bash
# Korean Ministry of Legislation API Key (your email) - Required
LEGISLATION_API_KEY=your_email@example.com

# API Base URLs (recommended to use default values)
LEGISLATION_SEARCH_URL=http://www.law.go.kr/DRF/lawSearch.do
LEGISLATION_SERVICE_URL=http://www.law.go.kr/DRF/lawService.do

# MCP Server Configuration
HOST=0.0.0.0
PORT=8001
TRANSPORT=stdio
LOG_LEVEL=INFO
MCP_SERVER_NAME=kr-legislation-mcp
```

> [!NOTE]
> `TRANSPORT` environment variable:
> - `stdio`: Default value, uses stdio transport
> - `http`: Runs in streamable-http mode (endpoint: `http://HOST:PORT/mcp`)

> **📋 API Key Information:**
> - The Korean Ministry of Legislation API is **free** to use
> - No registration or application process required - **only email address needed**
> - Enter your actual email address for `LEGISLATION_API_KEY`
> - Example: `LEGISLATION_API_KEY=user@gmail.com`

---

## Python 3.10+ Installation Guide

```bash
# Check Python version (must be 3.10 or higher)
python3 --version
```

If your Python version is lower than 3.10, follow the instructions below:

### macOS
```bash
# Using Homebrew
brew install python@3.10

# Or download from official website
# https://www.python.org/downloads/macos/
```

### Windows
- Download from [python.org](https://www.python.org/downloads/windows/)
- **Must check "Add Python to PATH" during installation**

### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install python3.10 python3.10-venv python3.10-distutils
```

### Linux (Fedora/CentOS/RHEL)
```bash
sudo dnf install python3.10
```

---

## Claude Desktop Setup

### Claude Desktop Integration

To use with Claude Desktop, you need to modify the configuration file:

**macOS Configuration File Location:**
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

**Windows Configuration File Location:**
```
%APPDATA%\Claude\claude_desktop_config.json
```

**Basic Configuration (stdio transport):**
```json
{
  "mcpServers": {
    "mcp-kr-legislation": {
      "command": "/your/path/mcp-kr-legislation/.venv/bin/mcp-kr-legislation",
      "env": {
        "LEGISLATION_API_KEY": "your_email@example.com",
        "PORT": "8001",
        "TRANSPORT": "stdio",
        "LOG_LEVEL": "INFO",
        "MCP_SERVER_NAME": "KR Legislation MCP"
      }
    }
  }
}
```

**Streamable HTTP Configuration (Optional):**
You can also run with streamable-http using HTTP transport:

```json
{
  "mcpServers": {
    "mcp-kr-legislation": {
      "command": "/your/path/mcp-kr-legislation/.venv/bin/mcp-kr-legislation",
      "env": {
        "LEGISLATION_API_KEY": "your_email@example.com",
        "HOST": "0.0.0.0",
        "PORT": "8001",
        "TRANSPORT": "http",
        "LOG_LEVEL": "INFO",
        "MCP_SERVER_NAME": "KR Legislation MCP"
      }
    }
  }
}
```

> [!NOTE]
> - `TRANSPORT=http` setting runs the server in streamable-http mode
> - Endpoint: `http://HOST:PORT/mcp`

> **⚠️ Important Notes:**
> - Update the `command` path to your actual virtual environment path
> - Replace `LEGISLATION_API_KEY` with your email address
> - The Korean Ministry of Legislation API is free and only requires an email address

---

## Usage

### Direct MCP Server Execution

```bash
mcp-kr-legislation
```

### Direct Use in Python

```python
from mcp_kr_legislation.apis.client import LegislationClient
from mcp_kr_legislation.config import legislation_config

# Initialize client
client = LegislationClient(config=legislation_config)

# Search legislation
result = client.search("law", {"query": "Labor Standards Act"})
print(result)

# Get legislation details
law_info = client.service("law", {"ID": "012345"})
print(law_info)
```

---

## 📊 Real Usage Examples

### 💼 Practical Use Cases

#### 1. Financial Company Personal Information Collection Legal Review
```
Question: "Can financial companies collect marital status information? Review related laws, enforcement decrees, and financial committee materials, and investigate if there are precedents to create a comprehensive report"

Sample Response:
🔗 API Call URL: http://www.law.go.kr/DRF/lawSearch.do?OC=test&type=JSON&target=law&query=Personal+Information+Protection+Act

🔍 'Personal Information Protection Act' Search Results
📊 Total 2 results found

📋 Detailed Legislation Information:

1. Personal Information Protection Act
   📝 Legislation Type: Act
   🏛️ Ministry: Personal Information Protection Commission
   🆔 Law ID: 011357
   📅 Promulgation Date: 2011-03-29
   ⏰ Enforcement Date: 2011-09-30
   🔗 Detail URL: http://www.law.go.kr/DRF/lawService.do?OC=test&type=JSON&target=law&ID=011357

💡 Additional Information:
- Increase the display parameter for more results
- Use the corresponding ID detail inquiry function for specific item details
- Full API response data can be verified directly via the above URL
```

#### 2. Constitutional Court Decision Search
```
Question: "Find Constitutional Court decisions related to freedom of expression"

Response: List of Constitutional Court decisions with detailed links and decision summaries for each case
```

#### 3. Administrative Trial Case Search
```
Question: "What are administrative trial cases for Personal Information Protection Act violations?"

Response: List of administrative trial cases with adjudication content and party information
```

### 🔬 Advanced Analysis Questions

- "Analyze the timeline of Personal Information Protection Act amendments over the past 5 years"
- "Compare differences in personal information-related decisions between Financial Services Commission and Personal Information Protection Committee"
- "How are personal information processing regulations structured in university regulations?"
- "Are there special administrative trial cases related to personal information at the Tax Tribunal?"

---

## ⚠️ Important Notes

- The Ministry of Legislation API is a free service, so please refrain from excessive requests
- Consult with experts for legal interpretation or legal advice
- This tool is for informational purposes and does not replace legal advice
- You can verify original data directly through API URLs included in each response

---

## 🆘 Troubleshooting

### Frequently Asked Questions

**Q: API key error occurs**
A: Check if you entered the correct email address in `LEGISLATION_API_KEY`.

**Q: No search results appear**
A: Try more specific search terms (e.g., use "Labor" instead of "Labor Standards Act")

**Q: Tools don't appear in Claude Desktop**
A: Check if the configuration file path and environment variables are correct, then restart Claude Desktop.

**Q: How do I use the URLs included in responses?**
A: You can open the API URLs included in responses directly in your browser to view the original JSON data.

---

## 📞 Support and Contribution

- **GitHub Issues**: [Issues Page](https://github.com/ChangooLee/mcp-kr-legislation/issues)
- **How to Contribute**: Contributions via Pull Requests are welcome
- **License**: MIT License

---

**📖 Related Projects**
- [MCP OpenDART](https://github.com/ChangooLee/mcp-opendart) - Korean Financial Supervisory Service Electronic Disclosure MCP Server
- [MCP Korean Real Estate](https://github.com/ChangooLee/mcp-kr-realestate) - Korean Real Estate Information MCP Server 