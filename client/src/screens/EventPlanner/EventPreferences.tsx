import React, { useState } from 'react';
import { Users, X, Minus, Plus, Edit2, Check } from 'lucide-react';

interface PartyMember {
  age: number;
  interest_weights: {
    [key: string]: number;
  };
}

interface FormData {
  party_type: string;
  party_members: {
    [key: string]: PartyMember;
  };
  vibe: string;
  budget_total: string;
  trip_start: string;
  trip_end: string;
  avoid_long_transit: number;
  prefer_outdoor: number;
  prefer_cultural: number;
  start_time: string;
  end_time: string;
}

const INTEREST_CATEGORIES = [
  'concerts', 'food', 'nightlife', 'history', 'museums', 'architecture',
  'aquarium', 'theme_parks', 'zoo', 'parks', 'islands', 'shopping',
  'pizza', 'theatre', 'views'
];

const PARTY_TYPES = {
  solo: { label: 'Solo', icon: '✈️' },
  couple: { label: 'Couple', icon: '❤️' },
  family: { label: 'Family', icon: '👨‍👩‍👧‍👦' },
  friends: { label: 'Friends', icon: '🎉' },
  multi_gen: { label: 'Multi-Gen', icon: '👴👶' }
};

const VIBES = [
  { value: 'family', label: 'Family', emoji: '🎠' },
  { value: 'urban', label: 'Urban', emoji: '🏙️' },
  { value: 'relaxed', label: 'Relaxed', emoji: '🌅' },
  { value: 'cultural', label: 'Cultural', emoji: '🏛️' },
  { value: 'active', label: 'Active', emoji: '🏃' },
  { value: 'leisurely', label: 'Leisurely', emoji: '☕' },
  { value: 'party', label: 'Party', emoji: '🎊' },
  { value: 'music', label: 'Music', emoji: '🎵' },
  { value: 'budget', label: 'Budget', emoji: '💰' }
];

export default function EventPreferences() {
  const [step, setStep] = useState(1);
  const [editingMember, setEditingMember] = useState<string | null>(null);
  const [tempName, setTempName] = useState('');
  const [formData, setFormData] = useState<FormData>({
    party_type: '',
    party_members: {},
    vibe: '',
    budget_total: '',
    trip_start: '',
    trip_end: '',
    avoid_long_transit: 5,
    prefer_outdoor: 5,
    prefer_cultural: 5,
    start_time: '',
    end_time: ''
  });

  const addPartyMember = () => {
    if (formData.party_type === 'solo' && Object.keys(formData.party_members).length >= 1) return;
    
    const newMemberName = `Member ${Object.keys(formData.party_members).length + 1}`;
    setFormData({
      ...formData,
      party_members: {
        ...formData.party_members,
        [newMemberName]: {
          age: 25,
          interest_weights: INTEREST_CATEGORIES.reduce((acc, cat) => ({...acc, [cat]: 5}), {})
        }
      }
    });
  };

  const removeMember = (memberName: string) => {
    const { [memberName]: removed, ...rest } = formData.party_members;
    setFormData({ ...formData, party_members: rest });
  };

  const startEditingName = (memberName: string) => {
    setEditingMember(memberName);
    setTempName(memberName);
  };

  const saveNameEdit = () => {
    if (!editingMember || !tempName.trim()) {
      setEditingMember(null);
      return;
    }

    const { [editingMember]: memberData, ...rest } = formData.party_members;
    setFormData({
      ...formData,
      party_members: {
        ...rest,
        [tempName]: memberData
      }
    });
    setEditingMember(null);
  };

  const updateMemberAge = (memberName: string, age: number) => {
    setFormData({
      ...formData,
      party_members: {
        ...formData.party_members,
        [memberName]: {
          ...formData.party_members[memberName],
          age: parseInt(age.toString()) || 0
        }
      }
    });
  };

  const incrementAge = (memberName: string) => {
    const currentAge = formData.party_members[memberName].age;
    updateMemberAge(memberName, currentAge + 1);
  };

  const decrementAge = (memberName: string) => {
    const currentAge = formData.party_members[memberName].age;
    if (currentAge > 0) updateMemberAge(memberName, currentAge - 1);
  };

  const updateMemberInterest = (memberName: string, interest: string, value: number) => {
    setFormData({
      ...formData,
      party_members: {
        ...formData.party_members,
        [memberName]: {
          ...formData.party_members[memberName],
          interest_weights: {
            ...formData.party_members[memberName].interest_weights,
            [interest]: parseInt(value.toString())
          }
        }
      }
    });
  };

  const canProceedStep1 = formData.party_type !== '';
  const canProceedStep2 = Object.keys(formData.party_members).length > 0;
  const canProceedStep3 = formData.vibe && formData.budget_total && formData.trip_start && formData.trip_end && formData.start_time && formData.end_time;

  const handleSubmit = () => {
    console.log('Final preferences:', formData);
    alert('Preferences saved! Check console.');
  };

  const totalSteps = 4;
  const progress = (step / totalSteps) * 100;

  return (
    <div style={{
    height: '100vh', 
    background: '#ffffff',
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    overflow: 'auto' 
    }}>
      {/* Progress bar */}
      <div style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        height: '4px',
        background: '#e5e7eb',
        zIndex: 100
      }}>
        <div style={{
          height: '100%',
          width: `${progress}%`,
          background: '#2F6BFF',
          transition: 'width 0.3s ease'
        }} />
      </div>

      {/* Scrollable container */}
      <div style={{
        maxWidth: '600px',
        margin: '0 auto',
        padding: '60px 20px 40px',
        height: '100vh',
        boxSizing: 'border-box'
        }}>
        {/* Header */}
        <div style={{
          textAlign: 'center',
          marginBottom: '40px'
        }}>
          <div style={{ fontSize: '48px', marginBottom: '12px' }}>✈️</div>
          <h1 style={{
            fontSize: '28px',
            fontWeight: '700',
            color: '#2F6BFF',
            margin: '0 0 8px 0'
          }}>
            Plan Your Trip
          </h1>
          <p style={{
            fontSize: '15px',
            color: '#555',
            margin: 0,
            fontWeight: '500'
          }}>
            Step {step} of {totalSteps}
          </p>
        </div>

        {/* Content card */}
        <div style={{
          background: '#ffffff',
          borderRadius: '12px',
          padding: '24px',
          boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
          border: '1px solid #e5e7eb',
          marginBottom: '20px'
        }}>
          {/* Step 1: Party Type */}
          {step === 1 && (
            <div>
              <h2 style={{
                fontSize: '20px',
                fontWeight: '700',
                color: '#333',
                marginTop: 0,
                marginBottom: '20px'
              }}>
                Who's traveling?
              </h2>
              
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(2, 1fr)',
                gap: '12px',
                marginBottom: '24px'
              }}>
                {Object.entries(PARTY_TYPES).map(([key, { label, icon }]) => (
                  <div
                    key={key}
                    onClick={() => setFormData({...formData, party_type: key})}
                    style={{
                      background: formData.party_type === key ? '#2F6BFF' : '#ffffff',
                      border: `1.5px solid ${formData.party_type === key ? '#2F6BFF' : '#CFCFD6'}`,
                      borderRadius: '12px',
                      padding: '20px 16px',
                      textAlign: 'center',
                      color: formData.party_type === key ? '#ffffff' : '#333',
                      fontWeight: '600',
                      cursor: 'pointer',
                      transition: 'all 0.2s',
                      userSelect: 'none'
                    }}
                  >
                    <div style={{ fontSize: '32px', marginBottom: '8px' }}>{icon}</div>
                    <div style={{ fontSize: '14px' }}>{label}</div>
                  </div>
                ))}
              </div>

              <button
                onClick={() => setStep(2)}
                disabled={!canProceedStep1}
                style={{
                  width: '100%',
                  height: '50px',
                  background: canProceedStep1 ? '#2F6BFF' : '#e5e7eb',
                  border: 'none',
                  borderRadius: '12px',
                  color: '#ffffff',
                  fontSize: '16px',
                  fontWeight: '600',
                  cursor: canProceedStep1 ? 'pointer' : 'not-allowed',
                  transition: 'all 0.2s'
                }}
              >
                Continue
              </button>
            </div>
          )}

          {/* Step 2: Party Members */}
          {step === 2 && (
            <div>
              <h2 style={{
                fontSize: '20px',
                fontWeight: '700',
                color: '#333',
                marginTop: 0,
                marginBottom: '20px'
              }}>
                Your travelers
              </h2>

              <div style={{ maxHeight: '60vh', overflowY: 'auto', marginBottom: '16px' }}>
                {Object.entries(formData.party_members).map(([memberName, memberData]) => (
                  <div key={memberName} style={{
                    background: '#f9fafb',
                    borderRadius: '12px',
                    padding: '20px',
                    marginBottom: '16px',
                    border: '1px solid #e5e7eb'
                  }}>
                    <div style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      marginBottom: '16px'
                    }}>
                      {editingMember === memberName ? (
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flex: 1 }}>
                          <input
                            type="text"
                            value={tempName}
                            onChange={(e) => setTempName(e.target.value)}
                            style={{
                              flex: 1,
                              padding: '8px 12px',
                              border: '1.5px solid #2F6BFF',
                              borderRadius: '8px',
                              fontSize: '14px',
                              fontWeight: '600'
                            }}
                            autoFocus
                          />
                          <button
                            onClick={saveNameEdit}
                            style={{
                              width: '32px',
                              height: '32px',
                              border: 'none',
                              background: '#2F6BFF',
                              borderRadius: '8px',
                              cursor: 'pointer',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center'
                            }}
                          >
                            <Check size={16} color="#ffffff" />
                          </button>
                        </div>
                      ) : (
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <div style={{
                            fontSize: '16px',
                            fontWeight: '700',
                            color: '#333'
                          }}>
                            {memberName}
                          </div>
                          <button
                            onClick={() => startEditingName(memberName)}
                            style={{
                              width: '24px',
                              height: '24px',
                              border: 'none',
                              background: 'transparent',
                              cursor: 'pointer',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center'
                            }}
                          >
                            <Edit2 size={14} color="#2F6BFF" />
                          </button>
                        </div>
                      )}
                      
                      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                        <div style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '8px',
                          background: '#ffffff',
                          border: '1.5px solid #CFCFD6',
                          borderRadius: '12px',
                          padding: '8px 12px'
                        }}>
                          <button
                            onClick={() => decrementAge(memberName)}
                            style={{
                              width: '32px',
                              height: '32px',
                              border: 'none',
                              background: '#f3f4f6',
                              borderRadius: '8px',
                              cursor: 'pointer',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center'
                            }}
                          >
                            <Minus size={16} color="#2F6BFF" />
                          </button>
                          <div style={{
                            fontSize: '20px',
                            fontWeight: '700',
                            color: '#2F6BFF',
                            minWidth: '40px',
                            textAlign: 'center'
                          }}>
                            {memberData.age}
                          </div>
                          <button
                            onClick={() => incrementAge(memberName)}
                            style={{
                              width: '32px',
                              height: '32px',
                              border: 'none',
                              background: '#f3f4f6',
                              borderRadius: '8px',
                              cursor: 'pointer',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center'
                            }}
                          >
                            <Plus size={16} color="#2F6BFF" />
                          </button>
                        </div>
                        
                        {Object.keys(formData.party_members).length > 1 && (
                          <button
                            onClick={() => removeMember(memberName)}
                            style={{
                              width: '32px',
                              height: '32px',
                              border: 'none',
                              background: '#fee2e2',
                              borderRadius: '8px',
                              cursor: 'pointer',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center'
                            }}
                          >
                            <X size={16} color="#dc2626" />
                          </button>
                        )}
                      </div>
                    </div>

                    <div style={{ display: 'grid', gap: '12px' }}>
                      {INTEREST_CATEGORIES.map(interest => (
                        <div key={interest}>
                          <div style={{
                            display: 'flex',
                            justifyContent: 'space-between',
                            marginBottom: '6px'
                          }}>
                            <label style={{
                              fontSize: '13px',
                              fontWeight: '600',
                              color: '#555',
                              textTransform: 'capitalize'
                            }}>
                              {interest.replace('_', ' ')}
                            </label>
                            <span style={{
                              fontSize: '13px',
                              fontWeight: '700',
                              color: '#2F6BFF'
                            }}>
                              {memberData.interest_weights[interest]}
                            </span>
                          </div>
                          <input
                            type="range"
                            min="0"
                            max="10"
                            value={memberData.interest_weights[interest]}
                            onChange={(e) => updateMemberInterest(memberName, interest, parseInt(e.target.value))}
                            style={{
                              width: '100%',
                              height: '6px',
                              borderRadius: '3px',
                              appearance: 'none',
                              background: `linear-gradient(90deg, #2F6BFF ${memberData.interest_weights[interest] * 10}%, #e5e7eb ${memberData.interest_weights[interest] * 10}%)`,
                              outline: 'none'
                            }}
                          />
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>

              {(formData.party_type !== 'solo' || Object.keys(formData.party_members).length === 0) && (
                <button
                  onClick={addPartyMember}
                  style={{
                    width: '100%',
                    height: '48px',
                    background: '#ffffff',
                    border: '1.5px solid #2F6BFF',
                    borderRadius: '12px',
                    color: '#2F6BFF',
                    fontSize: '15px',
                    fontWeight: '600',
                    cursor: 'pointer',
                    marginBottom: '16px'
                  }}
                >
                  + Add Person
                </button>
              )}

              <div style={{ display: 'flex', gap: '12px' }}>
                <button
                  onClick={() => setStep(1)}
                  style={{
                    flex: 1,
                    height: '50px',
                    background: '#ffffff',
                    border: '1.5px solid #CFCFD6',
                    borderRadius: '12px',
                    color: '#555',
                    fontSize: '16px',
                    fontWeight: '600',
                    cursor: 'pointer'
                  }}
                >
                  Back
                </button>
                <button
                  onClick={() => setStep(3)}
                  disabled={!canProceedStep2}
                  style={{
                    flex: 2,
                    height: '50px',
                    background: canProceedStep2 ? '#2F6BFF' : '#e5e7eb',
                    border: 'none',
                    borderRadius: '12px',
                    color: '#ffffff',
                    fontSize: '16px',
                    fontWeight: '600',
                    cursor: canProceedStep2 ? 'pointer' : 'not-allowed'
                  }}
                >
                  Continue
                </button>
              </div>
            </div>
          )}

          {/* Step 3: Trip Details */}
          {step === 3 && (
            <div>
              <h2 style={{
                fontSize: '20px',
                fontWeight: '700',
                color: '#333',
                marginTop: 0,
                marginBottom: '20px'
              }}>
                Trip details
              </h2>

              <div style={{ display: 'grid', gap: '20px', marginBottom: '24px' }}>
                <div>
                  <label style={{
                    display: 'block',
                    fontSize: '14px',
                    fontWeight: '600',
                    color: '#333',
                    marginBottom: '8px'
                  }}>
                    Vibe *
                  </label>
                  <div style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(3, 1fr)',
                    gap: '8px'
                  }}>
                    {VIBES.map(vibe => (
                      <div
                        key={vibe.value}
                        onClick={() => setFormData({...formData, vibe: vibe.value})}
                        style={{
                          background: formData.vibe === vibe.value ? '#2F6BFF' : '#ffffff',
                          border: `1.5px solid ${formData.vibe === vibe.value ? '#2F6BFF' : '#CFCFD6'}`,
                          borderRadius: '12px',
                          padding: '12px 8px',
                          textAlign: 'center',
                          color: formData.vibe === vibe.value ? '#ffffff' : '#333',
                          fontWeight: '600',
                          fontSize: '12px',
                          cursor: 'pointer',
                          userSelect: 'none'
                        }}
                      >
                        <div style={{ fontSize: '24px', marginBottom: '4px' }}>{vibe.emoji}</div>
                        <div>{vibe.label}</div>
                      </div>
                    ))}
                  </div>
                </div>

                <div>
                  <label style={{
                    display: 'block',
                    fontSize: '14px',
                    fontWeight: '600',
                    color: '#333',
                    marginBottom: '8px'
                  }}>
                    Start Date *
                  </label>
                  <input
                    type="date"
                    required
                    value={formData.trip_start}
                    onChange={(e) => setFormData({...formData, trip_start: e.target.value})}
                    style={{
                      width: '100%',
                      height: '48px',
                      padding: '0 12px',
                      border: '1.5px solid #CFCFD6',
                      borderRadius: '12px',
                      fontSize: '15px',
                      boxSizing: 'border-box'
                    }}
                  />
                </div>

                <div>
                  <label style={{
                    display: 'block',
                    fontSize: '14px',
                    fontWeight: '600',
                    color: '#333',
                    marginBottom: '8px'
                  }}>
                    End Date *
                  </label>
                  <input
                    type="date"
                    required
                    value={formData.trip_end}
                    onChange={(e) => setFormData({...formData, trip_end: e.target.value})}
                    style={{
                      width: '100%',
                      height: '48px',
                      padding: '0 12px',
                      border: '1.5px solid #CFCFD6',
                      borderRadius: '12px',
                      fontSize: '15px',
                      boxSizing: 'border-box'
                    }}
                  />
                </div>

                <div>
                  <label style={{
                    display: 'block',
                    fontSize: '14px',
                    fontWeight: '600',
                    color: '#333',
                    marginBottom: '8px'
                  }}>
                    Budget (CAD) *
                  </label>
                  <input
                    type="number"
                    required
                    placeholder="1000"
                    value={formData.budget_total}
                    onChange={(e) => setFormData({...formData, budget_total: e.target.value})}
                    style={{
                      width: '100%',
                      height: '48px',
                      padding: '0 12px',
                      border: '1.5px solid #CFCFD6',
                      borderRadius: '12px',
                      fontSize: '15px',
                      boxSizing: 'border-box'
                    }}
                  />
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                  <div>
                    <label style={{
                      display: 'block',
                      fontSize: '14px',
                      fontWeight: '600',
                      color: '#333',
                      marginBottom: '8px'
                    }}>
                      Start Time *
                    </label>
                    <input
                      type="time"
                      required
                      value={formData.start_time}
                      onChange={(e) => setFormData({...formData, start_time: e.target.value})}
                      style={{
                        width: '100%',
                        height: '48px',
                        padding: '0 12px',
                        border: '1.5px solid #CFCFD6',
                        borderRadius: '12px',
                        fontSize: '15px',
                        boxSizing: 'border-box'
                      }}
                    />
                  </div>
                  <div>
                    <label style={{
                      display: 'block',
                      fontSize: '14px',
                      fontWeight: '600',
                      color: '#333',
                      marginBottom: '8px'
                    }}>
                      End Time *
                    </label>
                    <input
                      type="time"
                      required
                      value={formData.end_time}
                      onChange={(e) => setFormData({...formData, end_time: e.target.value})}
                      style={{
                        width: '100%',
                        height: '48px',
                        padding: '0 12px',
                        border: '1.5px solid #CFCFD6',
                        borderRadius: '12px',
                        fontSize: '15px',
                        boxSizing: 'border-box'
                      }}
                    />
                  </div>
                </div>
              </div>

              <div style={{ display: 'flex', gap: '12px' }}>
                <button
                  onClick={() => setStep(2)}
                  style={{
                    flex: 1,
                    height: '50px',
                    background: '#ffffff',
                    border: '1.5px solid #CFCFD6',
                    borderRadius: '12px',
                    color: '#555',
                    fontSize: '16px',
                    fontWeight: '600',
                    cursor: 'pointer'
                  }}
                >
                  Back
                </button>
                <button
                  onClick={() => setStep(4)}
                  disabled={!canProceedStep3}
                  style={{
                    flex: 2,
                    height: '50px',
                    background: canProceedStep3 ? '#2F6BFF' : '#e5e7eb',
                    border: 'none',
                    borderRadius: '12px',
                    color: '#ffffff',
                    fontSize: '16px',
                    fontWeight: '600',
                    cursor: canProceedStep3 ? 'pointer' : 'not-allowed'
                  }}
                >
                  Continue
                </button>
              </div>
            </div>
          )}

          {/* Step 4: Preferences */}
          {step === 4 && (
            <div>
              <h2 style={{
                fontSize: '20px',
                fontWeight: '700',
                color: '#333',
                marginTop: 0,
                marginBottom: '20px'
              }}>
                Preferences
              </h2>

              <div style={{ display: 'grid', gap: '24px', marginBottom: '24px' }}>
                <div>
                  <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    marginBottom: '8px'
                  }}>
                    <label style={{
                      fontSize: '14px',
                      fontWeight: '600',
                      color: '#333'
                    }}>
                      Avoid long transit
                    </label>
                    <span style={{
                      fontSize: '16px',
                      fontWeight: '700',
                      color: '#2F6BFF'
                    }}>
                      {formData.avoid_long_transit}
                    </span>
                  </div>
                  <input
                    type="range"
                    min="1"
                    max="10"
                    value={formData.avoid_long_transit}
                    onChange={(e) => setFormData({...formData, avoid_long_transit: parseInt(e.target.value)})}
                    style={{
                      width: '100%',
                      height: '8px',
                      borderRadius: '4px',
                      appearance: 'none',
                      background: `linear-gradient(90deg, #2F6BFF ${formData.avoid_long_transit * 10}%, #e5e7eb ${formData.avoid_long_transit * 10}%)`,
                      outline: 'none'
                    }}
                  />
                </div>

                <div>
                  <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    marginBottom: '8px'
                  }}>
                    <label style={{
                      fontSize: '14px',
                      fontWeight: '600',
                      color: '#333'
                    }}>
                      Prefer outdoor
                    </label>
                    <span style={{
                      fontSize: '16px',
                      fontWeight: '700',
                      color: '#2F6BFF'
                    }}>
                      {formData.prefer_outdoor}
                    </span>
                  </div>
                  <input
                    type="range"
                    min="1"
                    max="10"
                    value={formData.prefer_outdoor}
                    onChange={(e) => setFormData({...formData, prefer_outdoor: parseInt(e.target.value)})}
                    style={{
                      width: '100%',
                      height: '8px',
                      borderRadius: '4px',
                      appearance: 'none',
                      background: `linear-gradient(90deg, #2F6BFF ${formData.prefer_outdoor * 10}%, #e5e7eb ${formData.prefer_outdoor * 10}%)`,
                      outline: 'none'
                    }}
                  />
                </div>

                <div>
                  <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    marginBottom: '8px'
                  }}>
                    <label style={{
                      fontSize: '14px',
                      fontWeight: '600',
                      color: '#333'
                    }}>
                      Prefer cultural
                    </label>
                    <span style={{
                      fontSize: '16px',
                      fontWeight: '700',
                      color: '#2F6BFF'
                    }}>
                      {formData.prefer_cultural}
                    </span>
                  </div>
                  <input
                    type="range"
                    min="1"
                    max="10"
                    value={formData.prefer_cultural}
                    onChange={(e) => setFormData({...formData, prefer_cultural: parseInt(e.target.value)})}
                    style={{
                      width: '100%',
                      height: '8px',
                      borderRadius: '4px',
                      appearance: 'none',
                      background: `linear-gradient(90deg, #2F6BFF ${formData.prefer_cultural * 10}%, #e5e7eb ${formData.prefer_cultural * 10}%)`,
                      outline: 'none'
                    }}
                  />
                </div>
              </div>

              <div style={{ display: 'flex', gap: '12px' }}>
                <button
                  onClick={() => setStep(3)}
                  style={{
                    flex: 1,
                    height: '50px',
                    background: '#ffffff',
                    border: '1.5px solid #CFCFD6',
                    borderRadius: '12px',
                    color: '#555',
                    fontSize: '16px',
                    fontWeight: '600',
                    cursor: 'pointer'
                  }}
                >
                  Back
                </button>
                <button
                  onClick={handleSubmit}
                  style={{
                    flex: 2,
                    height: '50px',
                    background: '#2F6BFF',
                    border: 'none',
                    borderRadius: '12px',
                    color: '#ffffff',
                    fontSize: '16px',
                    fontWeight: '600',
                    cursor: 'pointer'
                  }}
                >
                  Generate Itinerary
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}