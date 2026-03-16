'use client'

import { useState } from 'react'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import {
  faPlus,
  faSearch,
  faPaperPlane,
  faRobot,
  faFileAlt,
  faChartBar,
  faShieldAlt,
} from '@fortawesome/free-solid-svg-icons'
import { ragAPI, getAuthErrorMessage } from '@/lib/api'

type Message = {
  id: number
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  suggestions?: string[]
  citations?: string[]
}

export default function AuditCoPilotPage() {
  const [messages, setMessages] = useState<Message[]>([])
  const [inputValue, setInputValue] = useState('')
  const [isTyping, setIsTyping] = useState(false)

  const conversations = [
    { id: 1, title: 'Current conversation', lastMessage: messages.length ? 'Active' : 'No messages yet', unread: false },
  ]

  const handleSend = async () => {
    const text = inputValue.trim()
    if (!text) return

    const userMsg: Message = {
      id: messages.length + 1,
      role: 'user',
      content: text,
      timestamp: new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
    }
    setMessages((prev) => [...prev, userMsg])
    setInputValue('')
    setIsTyping(true)

    try {
      const data = await ragAPI.copilotQuery(text)
      const answer = data?.answer ?? (data?.success === false && data?.error ? data.error : 'No response from Co-Pilot.')
      const citations = Array.isArray(data?.citations) ? data.citations : undefined
      const assistantMsg: Message = {
        id: messages.length + 2,
        role: 'assistant',
        content: answer,
        timestamp: new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
        citations,
      }
      setMessages((prev) => [...prev, assistantMsg])
    } catch (err: unknown) {
      const errorContent = getAuthErrorMessage(err, 'Failed to get Co-Pilot response. Check that the RAG service is running and you are logged in.')
      setMessages((prev) => [
        ...prev,
        {
          id: messages.length + 2,
          role: 'assistant',
          content: `Error: ${errorContent}`,
          timestamp: new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
        },
      ])
    } finally {
      setIsTyping(false)
    }
  }

  return (
    <>
      <div className="flex h-[calc(100vh-64px)]">
        <div className="w-[30%] bg-surface border-r border-borderColor flex flex-col">
          <div className="p-6 border-b border-borderColor">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-textPrimary">Conversations</h2>
              <button className="w-9 h-9 flex items-center justify-center bg-primary hover:bg-primaryHover text-white rounded-lg">
                <FontAwesomeIcon icon={faPlus} />
              </button>
            </div>
            <div className="relative">
              <FontAwesomeIcon
                icon={faSearch}
                className="absolute left-3 top-1/2 transform -translate-y-1/2 text-textMuted text-sm"
              />
              <input
                type="text"
                placeholder="Search conversations..."
                className="w-full h-10 pl-9 pr-4 border border-borderColor rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
              />
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-4 space-y-2">
            {conversations.map((conv) => (
              <div
                key={conv.id}
                className={`p-4 rounded-lg cursor-pointer transition-colors ${
                  conv.id === 1
                    ? 'bg-indigo-50 border border-primary'
                    : 'hover:bg-gray-50 border border-transparent'
                }`}
              >
                <div className="flex items-start justify-between mb-2">
                  <h3 className="text-sm font-medium text-textPrimary">{conv.title}</h3>
                  {conv.unread && (
                    <span className="w-2 h-2 bg-primary rounded-full flex-shrink-0 mt-1"></span>
                  )}
                </div>
                <p className="text-xs text-textSecondary">{conv.lastMessage}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="flex-1 flex flex-col bg-bgPage">
          <div className="p-6 border-b border-borderColor bg-surface">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-primary rounded-lg flex items-center justify-center">
                <FontAwesomeIcon icon={faRobot} className="text-white" />
              </div>
              <div>
                <h1 className="text-lg font-semibold text-textPrimary">Audit Co-Pilot</h1>
                <p className="text-sm text-textSecondary">AI-powered audit assistant</p>
              </div>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[70%] ${
                    message.role === 'user'
                      ? 'bg-primary text-white rounded-2xl rounded-tr-sm p-4'
                      : 'bg-surface border border-borderColor rounded-2xl rounded-tl-sm p-4'
                  }`}
                >
                  {message.role === 'assistant' && (
                    <div className="flex items-center space-x-2 mb-2">
                      <FontAwesomeIcon icon={faRobot} className="text-primary" />
                      <span className="text-xs font-medium text-textSecondary">Audit Co-Pilot</span>
                    </div>
                  )}
                  <div
                    className={`text-sm whitespace-pre-wrap ${
                      message.role === 'user' ? 'text-white' : 'text-textPrimary'
                    }`}
                  >
                    {message.content}
                  </div>
                  {message.citations && message.citations.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-borderColor">
                      <p className="text-xs font-medium text-textSecondary mb-1">Sources:</p>
                      <ul className="text-xs text-textMuted space-y-0.5">
                        {message.citations.slice(0, 5).map((c: string, idx: number) => (
                          <li key={idx}>{c}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {message.suggestions && (
                    <div className="mt-4 space-y-2">
                      {message.suggestions.map((suggestion, idx) => (
                        <button
                          key={idx}
                          className="w-full text-left px-3 py-2 bg-indigo-50 hover:bg-indigo-100 text-primary text-xs font-medium rounded-lg transition-colors"
                        >
                          {suggestion}
                        </button>
                      ))}
                    </div>
                  )}
                  <div
                    className={`text-xs mt-2 ${
                      message.role === 'user' ? 'text-white/70' : 'text-textMuted'
                    }`}
                  >
                    {message.timestamp}
                  </div>
                </div>
              </div>
            ))}

            {isTyping && (
              <div className="flex justify-start">
                <div className="bg-surface border border-borderColor rounded-2xl rounded-tl-sm p-4">
                  <div className="flex items-center space-x-2">
                    <FontAwesomeIcon icon={faRobot} className="text-primary" />
                    <span className="text-xs font-medium text-textSecondary">Audit Co-Pilot</span>
                  </div>
                  <div className="flex items-center space-x-1 mt-2">
                    <div className="w-2 h-2 bg-textMuted rounded-full thinking-animation"></div>
                    <div className="w-2 h-2 bg-textMuted rounded-full thinking-animation" style={{ animationDelay: '0.2s' }}></div>
                    <div className="w-2 h-2 bg-textMuted rounded-full thinking-animation" style={{ animationDelay: '0.4s' }}></div>
                  </div>
                </div>
              </div>
            )}
          </div>

          <div className="p-6 border-t border-borderColor bg-surface">
            <div className="flex items-end space-x-3">
              <div className="flex-1">
                <textarea
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault()
                      handleSend()
                    }
                  }}
                  placeholder="Ask me anything about your audit data..."
                  rows={3}
                  className="w-full px-4 py-3 border border-borderColor rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent resize-none"
                />
                <div className="flex items-center justify-between mt-2">
                  <div className="flex items-center space-x-2">
                    <button className="p-2 text-textMuted hover:text-textPrimary hover:bg-gray-50 rounded-lg">
                      <FontAwesomeIcon icon={faFileAlt} />
                    </button>
                    <button className="p-2 text-textMuted hover:text-textPrimary hover:bg-gray-50 rounded-lg">
                      <FontAwesomeIcon icon={faChartBar} />
                    </button>
                    <button className="p-2 text-textMuted hover:text-textPrimary hover:bg-gray-50 rounded-lg">
                      <FontAwesomeIcon icon={faShieldAlt} />
                    </button>
                  </div>
                  <div className="text-xs text-textMuted">Press Enter to send, Shift+Enter for new line</div>
                </div>
              </div>
              <button
                onClick={handleSend}
                disabled={!inputValue.trim()}
                className="w-12 h-12 bg-primary hover:bg-primaryHover text-white rounded-lg flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <FontAwesomeIcon icon={faPaperPlane} />
              </button>
            </div>
          </div>
        </div>
      </div>
    </>
  )
}
