import Ember from 'ember';


export default Ember.Component.extend({
    usStates: [
        'Alabama',
        'Alaska',
        'Arizona',
        'Arkansas',
        'California',
        'Colorado',
        'Connecticut',
        'Delaware',
        'Florida',
        'Georgia',
        'Hawaii',
        'Idaho',
        'Illinois',
        'Indiana',
        'Iowa',
        'Kansas',
        'Kentucky',
        'Louisiana',
        'Maine',
        'Maryland',
        'Massachusetts',
        'Michigan',
        'Minnesota',
        'Mississippi',
        'Missouri',
        'Montana',
        'Nebraska',
        'Nevada',
        'New Hampshire',
        'New Jersey',
        'New Mexico',
        'New York',
        'North Carolina',
        'North Dakota',
        'Ohio',
        'Oklahoma',
        'Oregon',
        'Pennsylvania',
        'Rhode Island',
        'South Carolina',
        'South Dakota',
        'Tennessee',
        'Texas',
        'Utah',
        'Vermont',
        'Virginia',
        'Washington',
        'West Virginia',
        'Wisconsin',
        'Wyoming'
    ],
    labsByState: {
        "Alabama": [
            {
                'url': 'http://www.ches.ua.edu/hdfs/cdrc/',
                'name': 'University of Alabama Child Development Research Center'
            },
            {
                'url': 'http://monaelsheikh.com/',
                'name': 'Auburn University Child Sleep, Health, and Development Lab'
            }
        ],
        "Alaska": [],
        "Arizona": [
            {
                'url': 'http://web.arizona.edu/~tigger/',
                'name': 'University of Arizona Child Cognition Lab (Tigger Lab)'
            },
            {
                'url': 'http://web.arizona.edu/~tweety/',
                'name': 'University of Arizona Language Development Lab (Tweety Lab)'
            },
            {
                'url': 'http://nau.edu/SBS/IHD/Research/CDLL/',
                'name': 'Northern Arizona University Child Development and Language Lab'
            }
        ],
        "Arkansas": [
            {
                'url': 'http://acnc.uamsweb.com/research-2/our-laboratories-2/early-diets-and-long-term-health-lab/',
                'name': 'Arkansas Children\'s Nutrition Center Growth and Development Laboratory'
            }
        ],
        "California": [
            {
                'url': 'http://www.csus.edu/indiv/a/alexanderk/lab.htm',
                'name': 'CSU Sacramento Cognitive Development Lab'
            },
            {
                'url': 'http://www-psych.stanford.edu/~babylab/',
                'name': 'Stanford\'s Center for Infant Studies'
            },
            {
                'url': 'http://bungelab.berkeley.edu/participate/',
                'name': 'UC Berkeley Building Blocks of Cognition Lab'
            },
            {
                'url': 'http://babycenter.berkeley.edu/',
                'name': 'UC Berkeley Infant Studies Center'
            },
            {
                'url': 'http://psychology.berkeley.edu/participant-recruitment/rsvp-research-subject-volunteer-pool',
                'name': 'UC Berkeley Psychology Department (list of studies)'
            },
            {
                'url': 'http://oakeslab.ucdavis.edu/',
                'name': 'UC Davis Infant Cognition Lab'
            },
            {
                'url': ' http://languagelearninglab.dss.ucdavis.edu/',
                'name': 'UC Davis Language Learning Lab'
            },
            {
                'url': ' http://riveralab.ucdavis.edu/',
                'name': 'UC Davis Neurocognitive Development Lab'
            },
            {
                'url': 'http://www.cogsci.uci.edu/cogdev/information.html',
                'name': 'UC Irvine Sarnecka Cognitive Development Lab'
            },
            {
                'url': 'http://babytalk.psych.ucla.edu/home.htm',
                'name': 'UCLA Language and Cognitive Development Lab'
            },
            {
                'url': 'http://www.ccl.ucr.edu/',
                'name': 'UC Riverside Childhood Cognition Lab'
            },
            {
                'url': 'https://labs.psych.ucsb.edu/german/tamsin/',
                'name': 'UCSB Cognition & Development Laboratory'
            },
            {
                'url': 'http://www-cogsci.ucsd.edu/~deak/cdlab/',
                'name': 'UCSD Cognitive Development Lab'
            },
            {
                'url': 'http://dornsife.usc.edu/labs/mid-la/participate/',
                'name': 'USC Minds in Development Lab'
            }
        ],
        "Colorado": [
            {
                'url': 'http://sleep.colorado.edu/',
                'name': 'UC Boulder Sleep and Development Lab'
            },
            {
                'url': 'http://www.ucdenver.edu/academics/colleges/medicalschool/departments/psychiatry/Research/developmentalresearch/Pages/Overview.aspx',
                'name': 'University of Colorado Denver Developmental Psychiatry Research Group'
            },
            {
                'url': 'http://www.du.edu/psychology/child_health_and_development/',
                'name': 'University of Colorado Denver Child Health & Development Lab'
            },
            {
                'url': 'http://psych.colorado.edu/~cdc/whoweare.htm',
                'name': 'University of Colorado Denver Cognitive Development Center'
            }
        ],
        "Connecticut": [
            {
                'url': 'http://cogdev.research.wesleyan.edu/',
                'name': 'Wesleyan University Cognitive Development Labs'
            },
            {
                'url': 'http://infantandchild.yale.edu/',
                'name': 'Yale Infant and Child Research'
            },
            {
                'url': 'http://candlab.yale.edu/',
                'name': 'Yale Clinical Affective Neuroscience & Development Lab'
            },
            {
                'url': 'https://medicine.yale.edu/lab/mcpartland/',
                'name': 'McPartland Lab at Yale - Clinical Neuroscience of Autism Spectrum Disorder'
            }
        ],
        "Delaware": [
            {
                'url': 'http://www.udel.edu/ILP/about/team.html',
                'name': 'University of Delaware Infant Language Project'
            }
        ],
        "Florida": [
            {
                'url': 'http://casgroup.fiu.edu/dcn/pages.php?id=3636',
                'name': 'FIU Developmental Cognitive Neuroscience Lab'
            },
            {
                'url': 'http://online.sfsu.edu/devpsych/fair/index.html',
                'name': 'FSU Family Interaction Research Lab'
            },
            {
                'url': 'http://psy2.fau.edu/~lewkowicz/cdlfau/default.htm',
                'name': 'FAU Child Development Lab'
            },
            {
                'url': 'http://infantlab.fiu.edu/Infant_Lab.htm',
                'name': 'FIU Infant Development Lab'
            }
        ],
        "Georgia": [
            {
                'url': 'http://www.gcsu.edu/psychology/currentresearch.htm#Participate',
                'name': 'Georgia College Psychology Department'
            }
        ],
        "Hawaii": [
            {
                'url': 'http://www.psychology.hawaii.edu/concentrations/developmental-psychology.html',
                'name': 'University of Hawaii Developmental Psychology'
            }
        ],
        "Idaho": [],
        "Illinois": [
            {
                'url': 'http://internal.psychology.illinois.edu/~acimpian/',
                'name': 'University of Illinois Cognitive Development Lab'
            },
            {
                'url': 'http://internal.psychology.illinois.edu/infantlab/',
                'name': 'University of Illinois Infant Cognition Lab'
            },
            {
                'url': 'http://bradfordpillow.weebly.com/cognitive-development-lab.html',
                'name': 'Northern Illinois University Cognitive Development Lab'
            },
            {
                'url': 'http://www.childdevelopment.northwestern.edu/',
                'name': 'Northwestern University\'s Project on Child Development'
            },
            {
                'url': 'http://woodwardlab.uchicago.edu/Home.html',
                'name': 'University of Chicago Infant Learning and Development Lab'
            }
        ],
        "Indiana": [
            {
                'url': 'http://www.iub.edu/~cogdev/',
                'name': 'Indiana University Cognitive Development Lab'
            },
            {
                'url': 'http://www.psych.iupui.edu/Users/kjohnson/cogdevlab/INDEX.HTM',
                'name': 'IUPUI Cognitive Development Lab'
            },
            {
                'url': 'http://www.evansville.edu/majors/cognitivescience/language.cfm',
                'name': 'University of Evansville Language and Cognitive Development Laboratory'
            }
        ],
        "Iowa": [
            {
                'url': 'http://www.medicine.uiowa.edu/psychiatry/cognitivebraindevelopmentlaboratory/',
                'name': 'University of Iowa Cognitive Brain Development Laboratory'
            }
        ],
        "Kansas": [
            {
                'url': 'http://www2.ku.edu/~lsi/labs/neurocognitive_lab/staff.shtml',
                'name': 'KU Neurocognitive Development of Autism Research Laboratory'
            },
            {
                'url': 'http://healthprofessions.kumc.edu/school/research/carlson/index.html',
                'name': 'KU Maternal and Child Nutrition and Development Laboratory'
            },
            {
                'url': 'http://greenhoot.wordpress.com/meet-the-research-team/',
                'name': 'KU Memory and Development Lab'
            }
        ],
        "Minnesota": [
            {
                'url': 'http://www.cehd.umn.edu/icd/research/seralab/',
                'name': 'University of Minnesota Language and Cognitive Development Lab'
            },
            {
                'url': 'http://www.cehd.umn.edu/icd/research/cdnlab/',
                'name': 'University of Minnesota Cognitive Development & Neuroimaging Lab'
            },
            {
                'url': 'http://www.cehd.umn.edu/icd/research/carlson/',
                'name': 'University of Minnesota Carlson Child Development Lab'
            }
        ],
        "Kentucky": [
            {
                'url': 'http://babythinker.org',
                'name': 'University of Louisville Infant Cognition Lab'
            },
            {
                'url': 'http://www.wku.edu/psychological-sciences/labs/cognitive_development/index.php',
                'name': 'Western Kentucky University Cognitive Development Lab'
            }
        ],
        "Louisana": [],
        "Maine": [
            {
                'url': 'http://people.usm.maine.edu/bthompso/Site/Development%20Lab.html',
                'name': 'USM Human Development Lab'
            },
            {
                'url': 'http://www.colby.edu/psychology/labs/cogdev1/LabAlumni.html',
                'name': 'Colby Cognitive Development Lab'
            }
        ],
        "Maryland": [
            {
                'url': 'http://education.umd.edu/HDQM/labs/Fox/',
                'name': 'University of Maryland Child Development Lab'
            },
            {
                'url': 'http://ncdl.umd.edu/',
                'name': 'University of Maryland Neurocognitive Development Lab'
            }
        ],
        "Massachusetts": [
            {
                'url': 'http://eccl.mit.edu/',
                'name': 'MIT Early Childhood Cognition Lab'
            },
            {
                'url': 'http://gablab.mit.edu/',
                'name': 'MIT Gabrieli Lab'
            },
            {
                'url': 'http://saxelab.mit.edu/people.php',
                'name': 'MIT Saxelab Social Cognitive Neuroscience Lab'
            },
            {
                'url': 'https://software.rc.fas.harvard.edu/lds/',
                'name': 'Harvard Laboratory for Developmental Sciences'
            },
            {
                'url': 'http://www.bu.edu/cdl/',
                'name': 'Boston University Child Development Labs'
            },
            {
                'url': 'babies.umb.edu',
                'name': 'UMass Boston Baby Lab'
            },
            {
                'url': 'http://people.umass.edu/lscott/lab.htm',
                'name': 'UMass Amherst Brain, Cognition, and Development Lab'
            },
            {
                'url': 'http://www.northeastern.edu/berentlab/research/infant/',
                'name': 'Northeastern Infant Phonology Lab'
            }
        ],
        "Michigan": [
            {
                'url': 'http://www.educ.msu.edu/content/default.asp?contentID=903',
                'name': 'MSU Cognitive Development Lab'
            },
            {
                'url': 'http://ofenlab.wayne.edu/people.php',
                'name': 'Wayne State University Cognitive Brain Development Lab'
            }
        ],
        "Mississippi": [],
        "Missouri": [
            {
                'url': 'http://www.artsci.wustl.edu/~children/',
                'name': 'Washington University Cognition and Development Lab'
            },
            {
                'url': 'http://mumathstudy.missouri.edu/#content',
                'name': 'University of Missouri-Columbia Math Study'
            }
        ],
        "Montana": [
            {
                'url': 'http://hs.umt.edu/psychology/severson/',
                'name': 'The Minds Lab at University of Montana '
            },
            {
                'url': 'http://www.montana.edu/wwwpy/brooker/html/meet.html',
                'name': 'Montana State University DOME Lab'
            }
        ],
        "Nebraska": [
            {
                'url': 'http://www.boystownhospital.org/research/clinicalbehavioralstudies/Pages/LanguageDevelopmentLaboratory.aspx',
                'name': 'Boys Town National Research Hospital Language Development Laboratory'
            },
            {
                'url': 'http://research.unl.edu/dcn/',
                'name': 'University of Nebraska-Lincoln Developmental Cognitive Neuroscience Laboratory'
            }
        ],
        "Nevada": [
            {
                'url': 'http://www.unl.edu/dbrainlab/',
                'name': 'University of Nebraska-Lincoln Developmental Brain Lab'
            }
        ],
        "New Hampshire": [
            {
                'url': 'http://cola.unh.edu/news/frl',
                'name': 'University of New Hampshire Family Research Lab'
            }
        ],
        "New Jersey": [
            {
                'url': 'http://www.shu.edu/academics/gradmeded/ms-speech-language-pathology/dlc-lab.cfm',
                'name': 'Seton Hall University  Developmental Language and Cognition Laboratory'
            },
            {
                'url': 'http://www.ramapo.edu/sshs/childlab/',
                'name': 'Ramapo College Child Development Lab'
            },
            {
                'url': 'http://ruccs.rutgers.edu/~aleslie/',
                'name': 'Rutgers University Cognitive Development Lab'
            },
            {
                'url': 'http://babylab.rutgers.edu/HOME.html',
                'name': 'Rutgers University Infancy Studies Lab'
            },
            {
                'url': 'http://ruccs.rutgers.edu/languagestudies/people.html',
                'name': 'Rutgers University Lab for Developmental Language Studies'
            }
        ],
        "New Mexico": [],
        "New York": [
            {
                'url': 'http://www.columbia.edu/cu/needlab/',
                'name': 'Columbia Neurocognition, Early Experience, and Development (NEED) Lab'
            },
            {
                'url': 'https://www.facebook.com/pages/Child-Development-Lab-the-City-University-of-New-York/42978619994',
                'name': 'CUNY Child Development Lab'
            }
        ],
        "North Carolina": [
            {
                'url': 'http://people.uncw.edu/nguyens/',
                'name': 'UNCW Cognitive Development Lab'
            }
        ],
        "North Dakota": [
            {
                'url': 'http://www.cvcn.psych.ndsu.nodak.edu/labs/woods/',
                'name': 'NDSU Infant Cognitive Development Lab'
            }
        ],
        "Ohio": [
            {
                'url': 'http://cogdev.cog.ohio-state.edu/',
                'name': 'OSU Cognitive Development Lab'
            },
            {
                'url': 'http://www.ohio.edu/chsp/rcs/csd/research/dplab.cfm',
                'name': 'Ohio University Developmental Psycholinguistics Lab'
            }
        ],
        "Oklahoma": [],
        "Oregon": [
            {
                'url': 'http://bdl.uoregon.edu/Participants/participants.php',
                'name': 'University of Oregon Brain Development Lab'
            },
            {
                'url': 'http://www.uolearninglab.com',
                'name': 'University of Oregon Learning Lab'
            }
        ],
        "Pennsylvania": [
            {
                'url': 'http://www.temple.edu/infantlab/',
                'name': 'Temple Infant & Child Lab'
            },
            {
                'url': 'http://lncd.pitt.edu/wp/',
                'name': 'University of Pittsburgh Laboratory of Neurocognitive Development'
            },
            {
                'url': 'https://sites.sas.upenn.edu/cogdevlab/',
                'name': 'UPenn Cognition & Development Lab'
            },
            {
                'url': 'http://babylab.psych.psu.edu/',
                'name': 'Penn State Brain Development Lab'
            }
        ],
        "Rhode Island": [
            {
                'url': 'http://www.brown.edu/Research/dcnl/',
                'name': 'Brown University Developmental Cognitive Neuroscience Lab'
            }
        ],
        "South Carolina": [
            {
                'url': 'http://academicdepartments.musc.edu/joseph_lab/',
                'name': 'MUSC Brain, Cognition, & Development Lab'
            }
        ],
        "South Dakota": [],
        "Tennessee": [
            {
                'url': 'http://web.utk.edu/~infntlab/',
                'name': 'UT Knoxville Infant Perception-Action Lab'
            },
            {
                'url': 'http://peabody.vanderbilt.edu/departments/psych/research/research_labs/educational_cognitive_neuroscience_lab/index.php',
                'name': 'Vanderbilt Educational Cognitive Neuroscience Lab'
            }
        ],
        "Texas": [
            {
                'url': 'http://www.ccdlab.net/',
                'name': 'UT-Austin Culture, Cognition, & Development Lab'
            },
            {
                'url': 'http://homepage.psy.utexas.edu/HomePage/Group/EcholsLAB/',
                'name': 'UT-Austin Language Development Lab'
            },
            {
                'url': 'http://www.utexas.edu/cola/depts/psychology/areas-of-study/developmental/Labs--Affiliations/CRL.php',
                'name': 'UT-Austin Children\'s Research Lab'
            },
            {
                'url': 'http://www.uh.edu/class/psychology/dev-psych/research/cognitive-development/index.php',
                'name': 'University of Houston Cognitive Development Lab'
            }
        ],
        "Utah": [],
        "Vermont": [
            {
                'url': 'http://www.uvm.edu/psychology/?Page=developmental_labs.html&SM=researchsubmenu.html',
                'name': 'University of Vermont Developmental Laboratories (overview)'
            }
        ],
        "Virginia": [
            {
                'url': 'http://people.jmu.edu/vargakx/',
                'name': 'James Madison University Cognitive Development Lab'
            },
            {
                'url': 'http://www.psyc.vt.edu/labs/socialdev',
                'name': 'Virginia Tech Social Development Lab'
            },
            {
                'url': 'http://faculty.virginia.edu/childlearninglab/',
                'name': 'University of Virginia Child Language and Learning Lab'
            },
            {
                'url': 'http://denhamlab.gmu.edu/labmembers.html',
                'name': 'George Mason University Child Development Lab'
            }
        ],
        "Washington": [
            {
                'url': 'http://depts.washington.edu/eccl/',
                'name': 'University of Washington Early Childhood Cognition'
            },
            {
                'url': 'https://depts.washington.edu/uwkids/',
                'name': 'University of Washington Social Cognitive Development Lab'
            },
            {
                'url': 'http://ilabs.uw.edu/institute-faculty/bio/i-labs-andrew-n-meltzoff-phd',
                'name': 'University of Washington Infant and Child Studies Lab'
            }
        ],
        "West Virginia": [
            {
                'url': 'http://www.wvuadolescentlab.com/',
                'name': 'WVU Adolescent Development Lab'
            }
        ],
        "Wisconsin": [
            {
                'url': 'https://sites.google.com/site/haleyvlach/',
                'name': 'University of Wisconsin Learning, Cognition, & Development Lab'
            }
        ],
        "Wyoming": []
    },
    chosenState: '',
    labs: [],
    nothingToShow: false,
    matcher(state, term) {
        return state.toLowerCase().indexOf(term.trim().toLowerCase()) === 0;
    },
    actions: {
        chooseLocation(us_state) {
            this.set('chosenState', us_state);
            this.set('labs', this.get('labsByState')[us_state]);
            if(this.get('labs').length === 0){
                this.set('nothingToShow', true);
            } else{
                this.set('nothingToShow', false);
            }
        }
    }
});
