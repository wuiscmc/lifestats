require 'sinatra/base'
require 'json'

class MockServer < Sinatra::Base

  class FileServer
    attr_reader :collection

    def initialize
      @collection = [
          { offset: 0, filename: "1.json", offset_range: 0...658330804},
          { offset: 658330804, filename: "2.json", offset_range: 658330804...658330908},
          { offset: 658330908, filename: "3.json", offset_range: 658330908...658331014},
          { offset: 658331014, filename: "4.json", offset_range: 658331014...658331126},
          { offset: 658331126, filename: "5.json", offset_range: 658331126...658331229},
          { offset: 658331229, filename: "6.json", offset_range: 658331229...658331343},
          { offset: 658331343, filename: "7.json", offset_range: 658331343...658331445},
          { offset: 658331445, filename: "8.json", offset_range: 658331445...658331549},
          { offset: 658331549, filename: "9.json", offset_range: 658331549...658331651},
          { offset: 658331651, filename: "10.json", offset_range: 658331651...658331757},
          { offset: 658331757, filename: "11.json", offset_range: 658331757...658331858},
          { offset: 658331858, filename: "12.json", offset_range: 658331858...658331964},
          { offset: 658331964, filename: "13.json", offset_range: 658331964...658332068},
          { offset: 658332068, filename: "14.json", offset_range: 658332068...658332175},
          { offset: 658332175, filename: "15.json", offset_range: 658332175...658332277},
          { offset: 658332277, filename: "16.json", offset_range: 658332277...658332383},
          { offset: 658332383, filename: "17.json", offset_range: 658332383...658332486},
          { offset: 658332486, filename: "18.json", offset_range: 658332486...658332594},
          { offset: 658332594, filename: "19.json", offset_range: 658332594...658332699},
          { offset: 658332699, filename: "20.json", offset_range: 658332699...999999999},
        ]
    end

    def find(id)
      @collection.find { |file| file[:offset_range].cover?(id) }
    end
  end

  def initialize(*args)
    super
    @@counter ||= 0
    @@data_file_list ||= FileServer.new
  end

  get "/foodstats" do
    content_type :json
    file = @@data_file_list.find(params[:offset].to_i)
    file.nil? ? {} : file = File.read(File.dirname(__FILE__) + "/./#{file[:filename]}" )
  end

end

MockServer.run!