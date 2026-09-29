/** All user-facing copy lives here so Hindi/Marathi can be added. Use t(key). */
export type Lang = 'en' | 'hi' | 'mr'

const en = {
  home: 'Home',
  listings: 'Listings',
  leads: 'Leads',
  hello: 'Namaste',
  addListing: '+ Add listing',
  mySite: 'My website',
  open: 'Open',
  share: 'Share',
  shareWhatsapp: 'Share on WhatsApp',
  copyLink: 'Copy link',
  copied: 'Copied!',
  phoneLabel: 'Your mobile number',
  phonePlaceholder: '98765 43210',
  phoneInvalid: 'Enter a valid 10-digit Indian mobile number',
  sendOtp: 'Send OTP',
  otpLabel: 'Enter the 6-digit OTP',
  otpSentTo: 'OTP sent to',
  inviteLabel: 'Enter your 6-digit invite code',
  inviteFor: 'Invite code for',
  inviteHelp: 'Your personal code was sent to you on WhatsApp. No code yet? Message us and we will send one.',
  verify: 'Verify',
  resendIn: 'Resend OTP in',
  resend: 'Resend OTP',
  changeNumber: 'Change number',
  devHint: 'Dev only: OTP is',
  autofill: 'Fill it',
  yourName: 'Your name',
  yourCity: 'Your city',
  languages: 'Languages you speak',
  specialties: 'What do you sell?',
  createSite: 'Create my website',
  siteLive: 'Your website is live',
  addFirstListing: 'Add your first listing',
  goToStudio: 'Go to my app',
  loading: 'Please wait...',
  tryAgain: 'Try again',
  fixtureBanner: 'Demo mode: data is saved only on this phone',
  noListings: 'No listings yet. Add your first one!',
  noLeads: 'No leads yet. Share your listings to get enquiries.',
  hot: 'Hot',
  warm: 'Warm',
  cold: 'Cold',
  all: 'All',
  publish: 'Publish',
  markUnderOffer: 'Under offer',
  markSold: 'Mark sold',
  markRented: 'Mark rented',
  pause: 'Pause',
  makeLive: 'Make live',
  describe: 'Describe the property - e.g. 2 BHK in Baner, 85 lakh, ready possession',
  speak: 'Tap to speak',
  stopRecording: 'Tap to stop',
  recording: 'Recording',
  micDenied: 'Microphone permission was denied. You can type instead.',
  micUnsupported: 'Voice recording is not supported on this phone. Please type.',
  reRecord: 'Record again',
  addPhotos: 'Add photos',
  takePhoto: 'Take photo',
  next: 'Next',
  needSomething: 'Type, speak or add photos first',
  reading: 'Reading your description...',
  review: 'Check and confirm',
  pleaseCheck: 'Please check',
  required: 'Required to publish',
  transcript: 'What we heard',
  warnings: 'Please note',
  confirmPost: 'Confirm & post',
  posting: 'Posting...',
  posted: 'Your listing is live',
  postAnother: 'Add another listing',
  back: 'Back',
  save: 'Save',
  call: 'Call',
  whatsapp: 'WhatsApp',
  addNote: 'Add a note',
  notePlaceholder: 'e.g. wants to visit Sunday',
  timeline: 'Activity',
  notes: 'Notes',
  logout: 'Log out',
} as const

export type StringKey = keyof typeof en

const hi: Partial<Record<StringKey, string>> = {
  home: 'होम',
  listings: 'लिस्टिंग',
  leads: 'ग्राहक',
  hello: 'नमस्ते',
  addListing: '+ लिस्टिंग जोड़ें',
  shareWhatsapp: 'WhatsApp पर शेयर करें',
  sendOtp: 'OTP भेजें',
  verify: 'जाँचें',
}

const tables: Record<Lang, Partial<Record<StringKey, string>>> = { en, hi, mr: {} }
let current: Lang = 'en'

export function setLang(l: Lang) {
  current = l
}

export function t(key: StringKey): string {
  return tables[current][key] ?? en[key]
}
