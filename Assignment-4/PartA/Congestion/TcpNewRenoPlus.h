#ifndef TCP_NEWRENOPLUS_H
#define TCP_NEWRENOPLUS_H

#include "tcp-congestion-ops.h"
// #include "ns3/tcp-recovery-ops.h"
// #include "ns3/sequence-number.h"
// #include "ns3/traced-value.h"
// #include "ns3/event-id.h"

namespace ns3 {

// class Packet;
// class TcpHeader;
// class Time;
// class EventId;


class TcpNewRenoPlus : public TcpNewReno
{
public:
  /**
   * \brief Get the type ID.
   * \return the object TypeId
   */
  static TypeId GetTypeId (void);

  TcpNewRenoPlus (void);
  /**
   * \brief Copy constructor
   * \param sock the object to copy
   */
  TcpNewRenoPlus (const TcpNewRenoPlus& sock);
  virtual ~TcpNewRenoPlus (void);

  std::string GetName () const;
  virtual void IncreaseWindow (Ptr<TcpSocketState> tcb, uint32_t segmentsAcked);
  virtual uint32_t GetSsThresh (Ptr<const TcpSocketState> tcb,
                                uint32_t bytesInFlight);

  virtual Ptr<TcpCongestionOps> Fork ();

protected:
  virtual uint32_t SlowStart (Ptr<TcpSocketState> tcb, uint32_t segmentsAcked);
  virtual void CongestionAvoidance (Ptr<TcpSocketState> tcb, uint32_t segmentsAcked);      

};

} // namespace ns3

#endif /* TCP_NEWRENOPLUS_H */
